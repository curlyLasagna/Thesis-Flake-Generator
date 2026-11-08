#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "docling",
# ]
# ///
"""
Extracts contents from DOCX, PDF, and text documents via Docling with inline metadata.
Extracts clean markdown text and instructional context for student dev environments.
"""

import sys
import re
import json
import argparse
from pathlib import Path

# Instructional section headers to capture relevant setup/dependency context
INSTRUCTIONAL_SECTION_PATTERNS = [
    r"(?i)(?:prerequisites?|requirements?|environment|setup|installation|tools|getting\s+started|dependencies)"
]

def extract_content(file_path: Path, enable_ocr: bool = False) -> str:
    """Extract markdown text from PDF, DOCX, or text files using Docling, optimized for text without images."""
    suffix = file_path.suffix.lower()
    
    # Text-based file formats can be read directly
    text_extensions = {".txt", ".text", ".md", ".markdown", ".rst"}
    if suffix in text_extensions:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    # Attempt Docling extraction for PDF, DOCX, etc.
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat

        pipeline_options = PdfPipelineOptions(
            generate_page_images=False,
            generate_picture_images=False,
            do_picture_classification=False,
            do_picture_description=False,
            do_chart_extraction=False,
            do_ocr=enable_ocr
        )

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        conv_res = converter.convert(str(file_path.resolve()))
        return conv_res.document.export_to_markdown(image_placeholder="")
    except Exception as e:
        raise RuntimeError(f"Docling extraction failed for {file_path}: {e}") from e

def extract_instructional_context(content: str) -> list[str]:
    """Extract paragraphs or sections related to environment setup, prerequisites, or tools."""
    sections = []
    lines = content.splitlines()
    capturing = False
    current_chunk = []

    for line in lines:
        is_header = line.strip().startswith("#") or line.strip().isupper()
        matches_instruction = any(re.search(pat, line) for pat in INSTRUCTIONAL_SECTION_PATTERNS)

        if is_header and matches_instruction:
            if current_chunk:
                sections.append("\n".join(current_chunk).strip())
                current_chunk = []
            capturing = True
            current_chunk.append(line)
        elif is_header and capturing:
            # Reached a new header that might not be instructional
            if not matches_instruction:
                sections.append("\n".join(current_chunk).strip())
                current_chunk = []
                capturing = False
            else:
                current_chunk.append(line)
        elif capturing:
            current_chunk.append(line)

    if current_chunk:
        sections.append("\n".join(current_chunk).strip())

    return [s for s in sections if s]

def parse_document(file_path: Path, enable_ocr: bool = False):
    if not file_path.exists():
        print(f"ERROR: File '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    content = extract_content(file_path, enable_ocr=enable_ocr)
    instructional_sections = extract_instructional_context(content)

    return {
        "file_path": str(file_path.resolve()),
        "file_name": file_path.name,
        "format": file_path.suffix.lower().lstrip("."),
        "instructional_context": instructional_sections if instructional_sections else [content[:1000]],
        "extracted_content": content
    }

def main():
    parser = argparse.ArgumentParser(
        description="Extract contents from DOCX, PDF, and text files via Docling (ignoring images) for student dev environments"
    )
    parser.add_argument("doc_path", nargs="?", default=None, help="Path to document file (DOCX, PDF, or text)")
    parser.add_argument("--doc-path", dest="doc_path_opt", default=None, help="Alternative flag for document path")
    parser.add_argument("--raw", action="store_true", help="Output only the extracted raw markdown text")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for scanned PDFs (default: disabled for speed and text focus)")
    parser.add_argument("--output", "-o", default=None, help="Save extracted output to specified file")

    args = parser.parse_args()
    target_path_str = args.doc_path or args.doc_path_opt
    if not target_path_str:
        parser.print_help()
        sys.exit(1)

    target_path = Path(target_path_str)
    result = parse_document(target_path, enable_ocr=args.ocr)

    if args.raw:
        output_str = result["extracted_content"]
    else:
        output_str = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"Saved extracted output to: {args.output}")
    else:
        print(output_str)

if __name__ == "__main__":
    main()
