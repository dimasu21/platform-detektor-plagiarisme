import docx

# Create DOCX
doc = docx.Document()
doc.add_paragraph("Algoritma Rabin-Karp adalah algoritma pencarian string yang menggunakan hashing.")
doc.save("test_suspect.docx")

# Create TXT (as a simpler alternative since fpdf is not installed)
with open("test_source.txt", "w", encoding="utf-8") as f:
    f.write("Algoritma Rabin-Karp merupakan algoritma pencarian string yang memanfaatkan hashing untuk efisiensi.")

print("Test files created: test_suspect.docx, test_source.txt")
