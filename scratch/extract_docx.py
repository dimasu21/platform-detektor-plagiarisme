import docx
import sys

def extract_text(doc_path, txt_path):
    doc = docx.Document(doc_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for para in doc.paragraphs:
            f.write(para.text + '\n')

if __name__ == '__main__':
    extract_text(sys.argv[1], sys.argv[2])
