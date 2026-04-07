# main.py

ZIP files ke andar ke PDFs ko ek A4 sheet pe **4-up layout** (2×2 grid) me convert karta hai aur output ek naye folder me save karta hai.

---

## Features

- Folder ke saare `.zip` files automatically scan karta hai
- Har ZIP ke andar ke multiple PDFs support karta hai
- **4 pages = 1 A4 sheet** — maximum space utilize hota hai
- Pages ka aspect ratio preserve hota hai (stretch nahi hota)
- Har cell pe page number label hota hai
- Har ZIP ke liye alag output PDF banta hai
- Output ek naye folder me save hota hai (existing files overwrite nahi hote)

---

## Requirements

Python 3.8+ aur neeche diye libraries chahiye:

```bash
pip install pypdf reportlab
```

---

## Usage

```bash
python main.py --input_folder /path/to/zips --output_folder /path/to/output
```

### Arguments

| Argument | Description | Default |
|---|---|---|
| `--input_folder` | Folder jisme ZIP files hain | `.` (current directory) |
| `--output_folder` | Output PDFs kahan save hon | `./output_pdfs` |

### Examples

```bash
# Current folder ke ZIPs process karo, output ./output_pdfs me
python main.py

# Custom folders
python main.py --input_folder ./my_zips --output_folder ./results

# Absolute paths
python main.py --input_folder /home/dev/zips --output_folder /home/dev/output
```

---

## Output Structure

```
input_folder/
├── batch1.zip          ← Contains: a.pdf, b.pdf, c.pdf
├── batch2.zip          ← Contains: x.pdf, y.pdf, z.pdf

output_folder/
├── batch1_4up.pdf      ← batch1.zip ka output (4 pages per A4 sheet)
└── batch2_4up.pdf      ← batch2.zip ka output
```

---

## Layout

```
┌──────────────────────────┐
│  batch1.zip | Sheet 1/2  │  ← Header
├─────────────┬────────────┤
│   Page 1    │   Page 2   │
│             │            │
├─────────────┼────────────┤
│   Page 3    │   Page 4   │
│             │            │
└─────────────┴────────────┘
```

Agar source PDF me pages kam hain (jaise 3 pages), toh remaining cells blank rahenge.

---

## Notes

- ZIP ke andar nested folders bhi support hote hain — saare `.pdf` files dhundh leta hai
- `__MACOSX` hidden folders automatically skip ho jaate hain (macOS ZIP artifacts)
- Agar koi PDF corrupt/unreadable ho, usse skip karke baaki process hota rehta hai
- Output file naam: `<zip_name>_4up.pdf`

---

## License

Internal use — ICICI Bank FX Operations.