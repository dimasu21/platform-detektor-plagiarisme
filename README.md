# Platform Detektor Plagiarisme

Platform web untuk mendeteksi plagiarisme pada dokumen teks menggunakan algoritma **Rabin-Karp** dengan visualisasi highlight pada dokumen asli.

## 📋 Deskripsi

Sistem ini dirancang untuk Fakultas Ilmu Komputer untuk membantu mendeteksi kesamaan teks antara dokumen mahasiswa dengan dokumen referensi. Platform ini menggunakan algoritma Rabin-Karp untuk deteksi plagiarisme berbasis n-gram dan dilengkapi dengan visualisasi highlight menggunakan OCR (Optical Character Recognition).

## ✨ Fitur Utama

### 🔍 Deteksi Plagiarisme
- **Algoritma Rabin-Karp**: Deteksi plagiarisme berbasis rolling hash dan n-gram matching
- **Preprocessing Teks**: Stemming Bahasa Indonesia menggunakan PySastrawi
- **Multi-format Support**: 
  - Dokumen teks (.txt)
  - Microsoft Word (.docx)
  - PDF (.pdf)
  - Gambar (.jpg, .jpeg, .png) dengan OCR

### 🎨 Visualisasi Highlight
- **Visual Plagiarism Highlighting**: Tampilkan dokumen dengan highlight kotak merah pada bagian yang terdeteksi plagiat
- **OCR Integration**: Ekstraksi teks dan koordinat bounding box dari dokumen scan/gambar
- **Multi-page Support**: Vertical scrolling untuk dokumen multi-halaman
- **Download Support**: Unduh dokumen yang sudah di-highlight

### 👥 User Management
- **Authentication System**: Login dengan email dan password
- **User Registration**: Pendaftaran user baru
- **User Profiles**: Lihat dan edit profil user
- **Password Toggle**: Show/hide password dengan icon mata
- **Role-based Access**: Admin dan User role

### 🔐 Admin Dashboard
- **User Management**: Lihat, edit, dan hapus users
- **Role Management**: Toggle role antara Admin dan User
- **Statistics**: Total users, admin count, regular users count

## 🛠️ Teknologi yang Digunakan

### Backend
- **Python 3.x**
- **Flask 3.x**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: Session management
- **Werkzeug**: Password hashing

### Text Processing
- **PySastrawi**: Indonesian text stemming
- **Rabin-Karp Algorithm**: Plagiarism detection

### OCR & Image Processing
- **Tesseract OCR**: Text extraction dari gambar
- **pytesseract**: Python wrapper untuk Tesseract
- **Pillow (PIL)**: Image manipulation dan drawing
- **pdf2image**: Konversi PDF ke gambar
- **pypdf**: PDF text extraction

### Frontend
- **HTML5 & CSS3**: Professional academic styling
- **JavaScript**: Interactive features
- **Google Fonts**: Merriweather & Open Sans

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
# Install ke: D:\projectpribadi\tesseract.exe

# Install Poppler
# Download dari: https://github.com/oschwartz10612/poppler-windows/releases/
# Extract ke: D:\projectpribadi\poppler-25.11.0\
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

Sesuaikan path di `file_parser.py`:
```python
# Tesseract Configuration
pytesseract.pytesseract.tesseract_cmd = r'D:\projectpribadi\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'D:\projectpribadi\tessdata'

# Poppler Configuration  
POPPLER_PATH = r'D:\projectpribadi\poppler-25.11.0\Library\bin'
```

### 4. Inisialisasi Database
Database akan otomatis dibuat saat pertama kali menjalankan aplikasi.

### 5. Jalankan Aplikasi
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

### Login
1. Buka `http://127.0.0.1:5000`
2. Login dengan credentials admin atau register user baru
3. Klik icon mata untuk show/hide password

### Deteksi Plagiarisme
1. Login ke dashboard
2. Masukkan/upload dokumen **Suspect** (dokumen mahasiswa)
3. Masukkan/upload dokumen **Source** (dokumen referensi)
4. Klik tombol **Cek Plagiarisme**
5. Lihat hasil:
   - **Similarity Score**: Persentase kesamaan (%)
   - **Matched Phrases**: Daftar n-gram yang cocok
   - **Visual Highlights**: Dokumen dengan kotak merah pada bagian plagiat

### Download Hasil
- Klik tombol **Download Highlighted Images** untuk mengunduh semua halaman yang sudah di-highlight

### User Profile
1. Klik **Profile** di navigation bar
2. Edit nama atau ubah password
3. Simpan perubahan

### Admin Features (Admin Only)
1. Klik **Admin** di navigation bar
2. Lihat statistik users
3. Toggle role user (Admin ↔ User)
4. Hapus user (kecuali diri sendiri)

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
├── requirements.txt           # Python dependencies
├── plagiarism.db             # SQLite database
│
├── static/
│   ├── style.css             # CSS styling
│   └── uploads/
│       └── highlighted/      # Highlighted images storage
│
└── templates/
    ├── base.html             # Base template
    ├── login.html            # Login page
    ├── register.html         # Registration page
    ├── dashboard.html        # Main dashboard
    ├── profile.html          # User profile
    └── admin_users.html      # Admin user management
```

## 🎯 Algoritma Rabin-Karp

Platform ini menggunakan **Rabin-Karp algorithm** dengan konfigurasi:
- **N-gram size (k)**: 5 words
- **Rolling hash**: Polynomial hashing
- **Base**: 101 (prime number)
- **Modulo**: 10^9 + 9

### Cara Kerja:
1. **Preprocessing**: Stemming dan cleaning teks
2. **N-gram Generation**: Buat n-gram dari suspect dan source  
3. **Hashing**: Hash setiap n-gram menggunakan rolling hash
4. **Matching**: Compare hash values untuk deteksi kesamaan
5. **Similarity Calculation**: Hitung persentase kesamaan

## 🖼️ OCR & Highlighting

### OCR Pipeline:
1. Convert PDF/gambar ke format yang bisa di-process
2. Preprocessing gambar (grayscale, contrast enhancement)
3. Extract text dengan `pytesseract.image_to_data` (dengan bounding boxes)
4. Build word-to-box mapping

### Highlighting Pipeline:
1. Match n-gram phrases dengan OCR words
2. Find bounding boxes untuk matched phrases
3. Merge consecutive boxes
4. Draw red rectangles pada gambar
5. Save highlighted images

## 🔒 Security Features

- **Password Hashing**: Werkzeug bcrypt hashing
- **Session Management**: Flask-Login secure sessions
- **CSRF Protection**: Built-in Flask CSRF
- **Route Protection**: `@login_required` decorator
- **Admin Protection**: Role-based access control
- **Self-Protection**: Admin tidak bisa delete/edit diri sendiri

## 🎨 Design Highlights

- **Academic Professional Style**: Clean dan formal
- **Responsive Design**: Mobile-friendly layout
- **Large Input Fields**: Better UX dengan padding 16px
- **Password Toggle**: Eye icon untuk show/hide password
- **Visual Feedback**: Hover effects dan transitions
- **Color Scheme**: 
  - Primary: Academic Blue (#003366)
  - Accent: Gold (#d4af37)
  - Danger: Red untuk highlights

## 📊 Database Schema

**Users Table:**
```sql
- id (INTEGER PRIMARY KEY)
- email (VARCHAR UNIQUE NOT NULL)
- password_hash (VARCHAR)
- name (VARCHAR NOT NULL)
- role (VARCHAR DEFAULT 'user')
- profile_picture (VARCHAR)
- created_at (DATETIME)
- last_login (DATETIME)
```

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

### Database error
```bash
# Delete plagiarism.db dan restart aplikasi
rm plagiarism.db
python app.py
```

## 📝 License

This project is created for academic purposes at Fakultas Ilmu Komputer.

## 👨‍💻 Author

- **Platform Development**: Custom plagiarism detection system
- **Algorithms**: Rabin-Karp, Preprocessing, OCR Integration
- **Frontend**: Professional academic design

## 🙏 Credits

- **PySastrawi**: Indonesian text stemming
- **Tesseract OCR**: Text extraction
- **Flask**: Web framework
- **Rabin-Karp Algorithm**: Michael O. Rabin & Richard M. Karp

---

**Platform Detektor Plagiarisme** - Fakultas Ilmu Komputer © 2025
