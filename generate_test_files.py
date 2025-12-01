import docx
from fpdf import FPDF

# Create DOCX
doc = docx.Document()
doc.add_paragraph("Algoritma Rabin-Karp adalah algoritma pencarian string yang menggunakan hashing.")
doc.save("test_suspect.docx")

# Create PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Algoritma Rabin-Karp merupakan algoritma pencarian string yang memanfaatkan hashing untuk efisiensi.", ln=1, align="C")
pdf.output("test_source.pdf")

