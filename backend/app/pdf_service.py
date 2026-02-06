import fitz  # PyMuPDF
from typing import Dict, Tuple

def replace_text_in_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    replacements: Dict[str, str],
) -> Tuple[int, str]:
    """
    Strategy:
    - Find occurrences of each "from" string
    - Redact those rectangles
    - Insert replacement text in the same rectangle
    Notes:
    - Works best for text-based PDFs.
    - For scanned PDFs, you'd need OCR.
    """
    doc = fitz.open(input_pdf_path)
    replaced_count = 0

    for page_index in range(len(doc)):
        page = doc[page_index]

        for old, new in replacements.items():
            if not old:
                continue

            rects = page.search_for(old)
            if not rects:
                continue

            for rect in rects:
                # redact original
                page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

            # insert replacement text
            # (insert after redaction so it appears)
            rects_after = page.search_for(old)  # should be empty now, but keep logic simple
            # we still have original rects saved from before
            for rect in rects:
                page.insert_textbox(
                    rect,
                    new,
                    fontsize=10,
                    color=(0, 0, 0),
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                replaced_count += 1

    doc.save(output_pdf_path)
    doc.close()

    return replaced_count, ""
