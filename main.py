"""
ZIP to 4-up PDF Converter
--------------------------
Har ZIP file ke andar ke PDFs ko read karta hai aur
ek A4 page pe 4 PDF pages tile karke naya PDF banata hai.
Output ek naye folder me save hota hai.

Usage:
    python zip_to_4up_pdf.py --input_folder /path/to/zips --output_folder /path/to/output

Dependencies:
    pip install pypdf reportlab
"""

import os
import io
import zipfile
import argparse
import tempfile
from pathlib import Path

import pypdf
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# A4 dimensions in points (1 pt = 1/72 inch)
A4_W, A4_H = A4  # 595.28 x 841.89


def get_pdf_paths_from_zip(zip_path: Path, extract_dir: str) -> list[str]:
    """ZIP file se saare PDF files extract karke unke paths return karta hai."""
    pdf_paths = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in sorted(zf.namelist()):
            if name.lower().endswith(".pdf") and not name.startswith("__MACOSX"):
                extracted = zf.extract(name, extract_dir)
                pdf_paths.append(extracted)
    return pdf_paths


def collect_all_pages(pdf_paths: list[str]) -> list[tuple]:
    """
    Saare PDF files ke pages collect karta hai.
    Returns list of (PdfReader, page_index) tuples.
    """
    pages = []
    for pdf_path in pdf_paths:
        try:
            reader = PdfReader(pdf_path)
            for i in range(len(reader.pages)):
                pages.append((reader, i))
        except Exception as e:
            print(f"  [WARN] Could not read {pdf_path}: {e}")
    return pages


def create_4up_pdf(pages: list[tuple], output_path: str, zip_name: str):
    """
    4 pages ko ek A4 sheet pe tile karke PDF banata hai.
    Layout (2x2 grid):
        [ Page 1 ] [ Page 2 ]
        [ Page 3 ] [ Page 4 ]
    """
    writer = PdfWriter()
    MARGIN = 6          # points - border gap
    GAP = 4             # points - gap between tiles
    LABEL_H = 12        # points - height for page number label

    # Each cell size
    cell_w = (A4_W - 2 * MARGIN - GAP) / 2
    cell_h = (A4_H - 2 * MARGIN - GAP - LABEL_H) / 2

    # Cell origins (bottom-left of each cell) in PDF coordinate system
    # PDF Y=0 is at bottom, so top-left cell has higher Y
    cell_origins = [
        (MARGIN,              MARGIN + cell_h + GAP),   # Top-Left
        (MARGIN + cell_w + GAP, MARGIN + cell_h + GAP), # Top-Right
        (MARGIN,              MARGIN),                   # Bottom-Left
        (MARGIN + cell_w + GAP, MARGIN),                 # Bottom-Right
    ]

    total_pages = len(pages)
    sheet_count = (total_pages + 3) // 4  # ceil division

    print(f"  Total source pages : {total_pages}")
    print(f"  Output A4 sheets   : {sheet_count}")

    for sheet_idx in range(sheet_count):
        # Create blank A4 canvas in memory
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        # Draw thin border around entire sheet
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        c.rect(MARGIN / 2, MARGIN / 2, A4_W - MARGIN, A4_H - MARGIN)

        # Title / ZIP name at top
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        title = f"{zip_name}  |  Sheet {sheet_idx + 1} of {sheet_count}"
        c.drawCentredString(A4_W / 2, A4_H - MARGIN + 1, title)

        c.save()
        packet.seek(0)

        # Load the blank overlay page
        overlay_reader = PdfReader(packet)
        sheet_page = overlay_reader.pages[0]

        # Now tile up to 4 source pages onto this sheet
        for slot in range(4):
            src_idx = sheet_idx * 4 + slot
            if src_idx >= total_pages:
                break

            reader, page_idx = pages[src_idx]
            src_page = reader.pages[page_idx]

            # Source page dimensions
            src_w = float(src_page.mediabox.width)
            src_h = float(src_page.mediabox.height)

            if src_w == 0 or src_h == 0:
                continue

            # Scale to fit cell, preserving aspect ratio
            scale_x = cell_w / src_w
            scale_y = cell_h / src_h
            scale = min(scale_x, scale_y)

            scaled_w = src_w * scale
            scaled_h = src_h * scale

            cell_x, cell_y = cell_origins[slot]

            # Center within cell
            offset_x = cell_x + (cell_w - scaled_w) / 2
            offset_y = cell_y + (cell_h - scaled_h) / 2

            sheet_page.merge_transformed_page(
                src_page,
                Transformation().scale(scale).translate(offset_x, offset_y),
            )

            # Draw cell border
            border_packet = io.BytesIO()
            bc = canvas.Canvas(border_packet, pagesize=A4)
            bc.setStrokeColorRGB(0.8, 0.8, 0.8)
            bc.setLineWidth(0.3)
            bc.rect(cell_x, cell_y, cell_w, cell_h)
            # Page number label
            bc.setFont("Helvetica", 6)
            bc.setFillColorRGB(0.5, 0.5, 0.5)
            label = f"p.{src_idx + 1}"
            bc.drawString(cell_x + 2, cell_y + 2, label)
            bc.save()
            border_packet.seek(0)
            border_overlay = PdfReader(border_packet).pages[0]
            sheet_page.merge_page(border_overlay)

        writer.add_page(sheet_page)
        print(f"  Sheet {sheet_idx + 1}/{sheet_count} done", end="\r")

    print()  # newline after progress

    with open(output_path, "wb") as f:
        writer.write(f)


def process_folder(input_folder: str, output_folder: str):
    """
    Input folder ke saare ZIP files process karta hai.
    Har ZIP ke liye ek output PDF banata hai.
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    zip_files = sorted(input_path.glob("*.zip"))
    if not zip_files:
        print(f"[!] Koi ZIP file nahi mili: {input_folder}")
        return

    print(f"Found {len(zip_files)} ZIP file(s) in '{input_folder}'\n")

    for zip_file in zip_files:
        print(f"Processing: {zip_file.name}")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_paths = get_pdf_paths_from_zip(zip_file, tmpdir)

            if not pdf_paths:
                print(f"  [SKIP] No PDFs found inside {zip_file.name}\n")
                continue

            print(f"  Found {len(pdf_paths)} PDF(s) inside ZIP")

            pages = collect_all_pages(pdf_paths)

            if not pages:
                print(f"  [SKIP] No readable pages found.\n")
                continue

            out_name = zip_file.stem + "_4up.pdf"
            out_file = output_path / out_name

            create_4up_pdf(pages, str(out_file), zip_file.stem)
            print(f"  Saved -> {out_file}\n")

    print("Done! Saare ZIP process ho gaye.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ZIP ke PDFs ko A4 pe 4-up layout me convert karo"
    )
    parser.add_argument(
        "--input_folder",
        default=".",
        help="Folder jisme ZIP files hain (default: current directory)",
    )
    parser.add_argument(
        "--output_folder",
        default="./output_pdfs",
        help="Output PDFs kahan save hon (default: ./output_pdfs)",
    )
    args = parser.parse_args()

    process_folder(args.input_folder, args.output_folder)