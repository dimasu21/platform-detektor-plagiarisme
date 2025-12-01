# 🚀 Ngrok Setup - Public Access untuk Demo

## Apa itu Ngrok?

Ngrok membuat tunnel dari localhost ke internet, jadi aplikasi Flask yang running di komputer Anda bisa diakses dari mana saja via URL public.

**Perfect untuk:**
- ✅ Demo aplikasi ke orang lain
- ✅ Testing di mobile device
- ✅ Share ke dosen/client
- ✅ Temporary deployment (gratis!)

---

## 📦 Instalasi Ngrok

### Step 1: Download Ngrok

**Windows:**
1. Buka https://ngrok.com/download
2. Download versi Windows (ZIP file)
3. Extract ZIP ke folder (contoh: `D:\ngrok\`)

**Atau via Chocolatey:**
```bash
choco install ngrok
```

### Step 2: Signup Ngrok (Optional tapi Recommended)

1. Buka https://dashboard.ngrok.com/signup
2. Sign up gratis (bisa pakai Google/GitHub)
3. Copy **Authtoken** dari dashboard
4. Jalankan di terminal:
```bash
ngrok authtoken YOUR_AUTHTOKEN_HERE
```

**Keuntungan signup:**
- Unlimited connections
- Lebih stable
- Custom subdomain (paid)

---

## 🎯 Cara Menggunakan

### Step 1: Jalankan Flask App

```bash
# Di terminal pertama
cd D:\projectpribadi\platform-plagiarisme
python app.py
```

Server akan running di `http://127.0.0.1:5000`

### Step 2: Jalankan Ngrok

```bash
# Di terminal BARU (jangan tutup terminal Flask)
# Jika sudah di PATH:
ngrok http 5000

# Atau jika ngrok ada di folder D:\ngrok:
D:\ngrok\ngrok.exe http 5000
```

### Step 3: Copy Public URL

Ngrok akan tampilkan output seperti ini:
```
Session Status                online
Account                       dimasu (Free)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Public URL Anda:** `https://xxxx-xxxx-xxxx.ngrok-free.app`

### Step 4: Share & Test

1. Copy URL public (yang `https://xxxx....ngrok-free.app`)
2. Buka di browser mana saja (laptop/HP teman, dll)
3. Login dengan: `admin@plagiarism.local` / `Admin123!`
4. Test semua fitur

---

## 🎨 Ngrok Web Interface

Buka `http://127.0.0.1:4040` untuk monitoring:
- Request logs
- Response details
- Replay requests
- Debugging info

---

## ⚠️ Important Notes

### 1. URL Berubah Setiap Restart (Free)
- Free tier: URL random setiap kali restart ngrok
- Paid: Custom subdomain yang tetap

### 2. Keep Terminal Open
- Flask app **HARUS tetap running**
- Ngrok **HARUS tetap running**
- Jangan close kedua terminal!

### 3. Database Persistent
- Database di lokal (tidak hilang)
- Data tetap ada meski restart

### 4. Performance
- Latency tergantung koneksi internet
- Ngrok free cukup cepat untuk demo
- Max connections di free tier: unlimited (dengan authtoken)

---

## 🔧 Tips & Tricks

### Auto-restart Ngrok dengan Script

Buat file `start_ngrok.bat`:
```batch
@echo off
echo Starting Flask App...
start cmd /k "cd D:\projectpribadi\platform-plagiarisme && python app.py"

timeout /t 5

echo Starting Ngrok...
start cmd /k "ngrok http 5000"

echo.
echo ========================================
echo   Platform Detektor Plagiarisme
echo ========================================
echo   Flask App: http://127.0.0.1:5000
echo   Ngrok Dashboard: http://127.0.0.1:4040
echo ========================================
pause
```

Double-click untuk start semua sekaligus!

### Region Selection

Default: Asia Pacific sudah bagus untuk Indonesia

Jika mau ganti region:
```bash
ngrok http 5000 --region ap  # Asia Pacific
ngrok http 5000 --region us  # United States
ngrok http 5000 --region eu  # Europe
```

### Custom Subdomain (Paid)

```bash
ngrok http 5000 --subdomain=plagiarisme-demo
# URL: https://plagiarisme-demo.ngrok.io
```

---

## 🐛 Troubleshooting

### "ngrok is not recognized"

**Fix:**
```bash
# Use full path
D:\ngrok\ngrok.exe http 5000

# Atau add ke PATH:
# 1. Search "Environment Variables"
# 2. Edit "Path"
# 3. Add "D:\ngrok"
# 4. Restart terminal
```

### "Failed to listen on port 5000"

Flask belum running atau port bentrok:
```bash
# Check port 5000
netstat -ano | findstr :5000

# Atau ganti port Flask
# Di app.py ubah ke: app.run(debug=True, port=5001)
# Lalu: ngrok http 5001
```

### "Tunnel not found"

Free tier kadang kena rate limit. Tunggu beberapa menit atau signup untuk authtoken.

### Database Error

```bash
# Reset database
del plagiarism.db
python app.py  # Will recreate database
```

---

## 📊 Demo Checklist

Sebelum demo, pastikan:

- [ ] Flask app running di `http://127.0.0.1:5000`
- [ ] Ngrok running dengan public URL
- [ ] Test public URL di browser
- [ ] Login berhasil dengan admin credentials
- [ ] Test upload PDF & plagiarism detection
- [ ] Test visual highlighting
- [ ] Test user registration
- [ ] Check internet connection stable
- [ ] Battery laptop full (jika demo offline)

---

## 💰 Ngrok Pricing

**Free:**
- ✅ 1 online ngrok process
- ✅ 4 tunnels/ngrok process
- ✅ 40 connections/minute
- ✅ Random URLs
- ⚠️ URL berubah setiap restart

**Personal ($8/month):**
- ✅ Custom subdomains
- ✅ Reserved domains
- ✅ More connections
- ✅ IP whitelisting

**For demo/testing: FREE is enough!**

---

## 🎯 Alternative untuk Production

Ngrok bagus untuk demo, tapi untuk production gunakan:
- **Railway**: $5 credit/month
- **Fly.io**: Free tier dengan persistent disk
- **Heroku**: $7/month
- **VPS**: DigitalOcean, Linode ($5-10/month)

---

## 📞 Support

- **Ngrok Docs**: https://ngrok.com/docs
- **Dashboard**: https://dashboard.ngrok.com
- **Status**: https://status.ngrok.com

---

## ✅ Quick Start Commands

```bash
# Terminal 1: Start Flask
python app.py

# Terminal 2: Start Ngrok
ngrok http 5000

# Copy public URL dari output ngrok
# Share URL ke siapa saja!
```

**Done! Aplikasi bisa diakses dari internet!** 🌐
