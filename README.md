# Platform Detektor Plagiarisme

Platform web untuk mendeteksi plagiarisme pada dokumen teks menggunakan algoritma **Rabin-Karp** dengan visualisasi highlight pada dokumen asli.

## 📋 Deskripsi

Sistem ini dirancang untuk Fakultas Ilmu Komputer untuk membantu mendeteksi kesamaan teks antara dokumen mahasiswa dengan dokumen referensi. Platform ini menggunakan algoritma Rabin-Karp untuk deteksi plagiarisme berbasis n-gram dan dilengkapi dengan visualisasi highlight menggunakan OCR (Optical Character Recognition).

## ✨ Fitur Utama

### 🔍 Deteksi Plagiarisme dengan Rabin-Karp K-Gram
- **Algoritma Rabin-Karp**: Deteksi plagiarisme berbasis rolling hash dan K-Gram (k=5)
- **Preprocessing Teks**: Stemming Bahasa Indonesia menggunakan PySastrawi
- **Multi-format Support**: 
  - Dokumen teks (.txt)
  - Microsoft Word (.docx)
  - PDF (.pdf)
  - Gambar (.jpg, .jpeg, .png) dengan OCR

### 📄 Compare (Perbandingan 2 Dokumen)
- Upload atau paste teks untuk membandingkan 2 dokumen
- Hasil similarity score dengan interpretasi (0-100%)
- Visual highlight teks yang cocok (warna kuning)
- OCR highlight dengan kotak merah pada dokumen gambar/PDF

### 📑 Multi Compare (Batch hingga 30 File)
- Upload hingga 30 file sekaligus
- Perbandingan semua pasangan dokumen secara otomatis
- Statistik: Total perbandingan, rata-rata similarity, similarity tertinggi
- Lihat detail perbandingan untuk setiap pasangan
- Visual highlight OCR dengan kotak merah

### 🖼️ OCR untuk Gambar/PDF
- Ekstraksi teks otomatis dari gambar dan PDF scan
- Preprocessing gambar untuk akurasi OCR lebih baik
- Multi-page support untuk dokumen PDF
- Download hasil dengan highlight

### 🎨 Visual Highlight
- **Kotak Merah**: Menandai area plagiarisme pada dokumen gambar/PDF
- **Teks Kuning**: Menandai frasa yang cocok pada perbandingan teks
- Download dokumen yang sudah di-highlight

### 📊 Score Interpretation (Panduan Interpretasi Skor)
| Skor | Level | Interpretasi |
|------|-------|--------------|
| 90-100% | 🔴 Tinggi | Terindikasi kuat plagiarisme - Perlu ditinjau segera |
| 60-89% | 🟡 Mencurigakan | Perlu investigasi lebih lanjut |
| 30-59% | 🟢 Rendah | Beberapa frasa umum terdeteksi |
| 0-29% | ✅ Aman | Minimal atau tidak ada plagiarisme |

### 📱 Responsive Mobile dengan Hamburger Menu
- Desain responsif untuk semua ukuran layar
- Hamburger menu untuk navigasi mobile
- Layout adaptif untuk tablet dan smartphone

### 👥 User Authentication
- **Login/Register**: Autentikasi dengan email dan password
- **User Profiles**: Lihat dan edit profil user
- **Password Toggle**: Show/hide password
- **Role-based Access**: Admin dan User role
- **Admin Dashboard**: Kelola users dan lihat statistik

## 🎨 Desain UI

- **Futuristic Minimalist Design**: Clean dan modern
- **Color Scheme**:
  - Primary Dark: #191A23
  - Accent Lime: #B9FF66
  - Background: White/Light Gray
- **Typography**: Space Grotesk (Google Fonts)
- **Large Rounded Corners**: Border radius modern
- **Responsive**: Mobile-first approach

## 🛠️ Teknologi yang Digunakan

### Backend
- **Python 3.x**
- **Flask 3.x**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: Session management
- **Werkzeug**: Password hashing

### Text Processing
- **PySastrawi**: Indonesian text stemming
- **Rabin-Karp Algorithm**: Plagiarism detection dengan K-Gram

### OCR & Image Processing
- **Tesseract OCR**: Text extraction dari gambar
- **pytesseract**: Python wrapper untuk Tesseract
- **Pillow (PIL)**: Image manipulation dan drawing
- **pdf2image**: Konversi PDF ke gambar
- **pypdf**: PDF text extraction

### Frontend
- **HTML5 & CSS3**: Modern styling
- **JavaScript**: Interactive features
- **Google Fonts**: Space Grotesk

## 📦 Requirements

### Software Dependencies
```
Python 3.8+
Tesseract OCR
Poppler (untuk pdf2image)
```

### Python Packages
```
Flask==3.0.0
PySastrawi==1.2.0
python-docx==1.1.0
pypdf==3.17.0
pytesseract==0.3.10
Pillow==10.0.1
pdf2image==1.16.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
python-dotenv==1.0.0
```

## 🚀 Instalasi

### 1. Clone Repository
```bash
git clone <repository-url>
cd platform-plagiarisme
```

### 2. Install Dependencies

#### Windows
```bash
# Install Python packages
pip install -r requirements.txt

# Install Tesseract OCR
# Download dari: https://github.com/UB-Mannheim/tesseract/wiki

# Install Poppler
# Download dari: https://github.com/oschwartz10612/poppler-windows/releases/
```

#### Linux/Mac
```bash
# Install Python packages
pip install -r requirements.txt

# Install Tesseract
sudo apt-get install tesseract-ocr tesseract-ocr-ind  # Ubuntu/Debian
brew install tesseract tesseract-lang  # macOS

# Install Poppler
sudo apt-get install poppler-utils  # Ubuntu/Debian
brew install poppler  # macOS
```

### 3. Setup Environment Variables

Sesuaikan path di `file_parser.py` jika lokasi instalasi berbeda:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler\Library\bin'
```

### 4. Jalankan Aplikasi
```bash
python app.py
```

Akses di browser: `http://127.0.0.1:5000`

## 🔑 Default Credentials

**Admin Account:**
- Email: `admin@plagiarism.local`
- Password: `Admin123!`

> ⚠️ **PENTING**: Ubah password default setelah login pertama kali!

## 📖 Cara Penggunaan

### Compare (2 Dokumen)
1. Login ke dashboard
2. Masukkan/upload dokumen **Jawaban Mahasiswa**
3. Masukkan/upload dokumen **Kunci Jawaban/Jawaban lainnya**
4. Klik **Cek Plagiarisme**
5. Lihat hasil: Similarity Score, Visual Highlights, Matched Phrases

### Multi Compare (Batch)
1. Klik menu **Multi Compare**
2. Upload 2-30 file dokumen
3. Klik **Jalankan Perbandingan**
4. Lihat statistik dan daftar semua perbandingan
5. Klik pasangan untuk melihat detail dengan highlight

## 📁 Struktur Project

```
platform-plagiarisme/
│
├── app.py                      # Main Flask application
├── models.py                   # Database models (User)
├── database.py                 # Database utilities
├── rabin_karp.py              # Rabin-Karp algorithm
├── preprocessing.py            # Text preprocessing & stemming
├── file_parser.py             # File extraction & OCR
├── highlight_visualizer.py    # Visual highlighting logic
├── text_highlighter.py        # Text highlighting for web
├── batch_comparison.py        # Batch comparison logic
├── requirements.txt           # Python dependencies
├── plagiarism.db             # SQLite database
│
├── static/
│   ├── style.css             # CSS styling
│   └── uploads/              # Uploaded & highlighted images
│
└── templates/
    ├── base.html             # Base template dengan hamburger menu
    ├── login.html            # Login page
    ├── register.html         # Registration page
    ├── dashboard.html        # Compare page
    ├── batch.html            # Multi Compare page
    ├── batch_detail.html     # Batch comparison detail
    ├── profile.html          # User profile
    └── admin_users.html      # Admin user management
```

## 🎯 Algoritma Rabin-Karp K-Gram

Platform ini menggunakan **Rabin-Karp algorithm** dengan konfigurasi:
- **K-Gram size**: 5 words
- **Rolling hash**: Polynomial hashing
- **Base**: 101 (prime number)
- **Modulo**: 10^9 + 9

### Cara Kerja:
1. **Preprocessing**: Stemming dan cleaning teks
2. **K-Gram Generation**: Buat K-Gram dari kedua dokumen
3. **Hashing**: Hash setiap K-Gram menggunakan rolling hash
4. **Matching**: Compare hash values untuk deteksi kesamaan
5. **Similarity Calculation**: Hitung persentase kesamaan

## 🔒 Security Features

- **Password Hashing**: Werkzeug bcrypt hashing
- **Session Management**: Flask-Login secure sessions
- **Route Protection**: `@login_required` decorator
- **Admin Protection**: Role-based access control

## 🐛 Troubleshooting

### ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Tesseract not found
```bash
# Windows: Install Tesseract dan set path di file_parser.py
# Linux: sudo apt-get install tesseract-ocr tesseract-ocr-ind
```

### PDF conversion error
```bash
# Install Poppler dan set POPPLER_PATH di file_parser.py
```

## 📝 License

This project is created for academic purposes at Fakultas Ilmu Komputer.

## 👨‍💻 Author

**Dimas Tri M** - Platform Detektor Plagiarisme © 2025

---

**Platform Detektor Plagiarisme** - Deteksi Plagiarisme dengan Rabin-Karp K-Gram
