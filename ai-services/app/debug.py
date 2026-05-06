"""
Simulate: what would the re-chunked PDF look like for the Luxemburg query?
Find chunks containing 'luxemburg' and show them.
"""

from app.ingestion.loader import load_pdf
from app.ingestion.splitter import split_text
import glob

# Find the uploaded PDF
upload_dir = "data/uploads"
pdfs = glob.glob(f"{upload_dir}/*.pdf")
if not pdfs:
    print("No PDFs found in data/uploads/")
    exit(1)

pdf_path = pdfs[0]
print(f"PDF: {pdf_path}")
print(f"New chunk size: 500 chars, overlap: 100")
print("=" * 60)

text = load_pdf(pdf_path)
chunks = split_text(text, "test")

print(f"Total chunks: {len(chunks)} (was ~50 at 1000 chars)\n")

# Find chunks mentioning Luxemburg
lux_chunks = [c for c in chunks if "luxemburg" in c["content"].lower()]
print(f"Chunks containing 'Luxemburg': {len(lux_chunks)}\n")

for c in lux_chunks:
    print(f"--- Chunk #{c['metadata']['chunk_index']} ---")
    print(c["content"][:400])
    print()
