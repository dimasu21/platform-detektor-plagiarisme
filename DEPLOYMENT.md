# 🚀 Panduan Deploy ke Render.com

## Persiapan

### 1. Update File Parser untuk Production
Pastikan path Tesseract sudah di-update di `file_parser.py`:

```python
# Akan otomatis detect di Linux (Render)
pytesseract.pytesseract.tesseract_cmd = 'tesseract'  # Default Linux path
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata'
```

### 2. Push ke GitHub
```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

## Deployment Steps

### Step 1: Create Render Account
1. Buka https://render.com
2. Sign up / Login dengan GitHub account
3. Authorize Render to access your repositories

### Step 2: Create New Web Service
1. Klik **"New +"** button
2. Pilih **"Web Service"**
3. Connect repository: `dimasu21/platform-detektor-plagiarisme`
4. Klik **"Connect"**

### Step 3: Configure Service
Render akan otomatis detect `render.yaml`, atau manual:

**Basic Settings:**
- **Name**: `platform-detektor-plagiarisme`
- **Region**: Singapore (atau terdekat)
- **Branch**: `main`
- **Environment**: `Docker`

**Build Settings:**
- **Dockerfile Path**: `./Dockerfile`
- Auto-detected dari render.yaml

**Environment Variables:**
- `SECRET_KEY`: (auto-generated) atau set manual
- `FLASK_ENV`: `production`

### Step 4: Deploy
1. Klik **"Create Web Service"**
2. Wait for build (5-10 minutes first time)
3. Monitor logs untuk errors

### Step 5: Verify Deployment
1. Klik URL yang diberikan Render (e.g., `https://platform-detektor-plagiarisme.onrender.com`)
2. Test login dengan credentials admin
3. Test upload & plagiarism detection

## ⚠️ Important Notes

### Database Persistence
**Problem**: SQLite database akan hilang setiap redeploy di free tier.

**Solutions:**

**Option A: Use Render PostgreSQL (Recommended)**
1. Create PostgreSQL database di Render
2. Update `app.py`:
```python
# Change from SQLite to PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///plagiarism.db'
```
3. Add to requirements.txt:
```
psycopg2-binary==2.9.9
```

**Option B: Use Render Disk (Paid)**
- Mount persistent disk di `/data`
- Change database path ke `/data/plagiarism.db`

**Option C: Keep SQLite (Low Priority Data)**
- Database reset setiap deploy
- OK untuk testing/demo

### File Uploads Persistence
Sama seperti database, `static/uploads/` akan hilang setiap redeploy.

**Solution**: Use cloud storage
- AWS S3
- Cloudinary
- Render Disk (paid)

## 🐛 Troubleshooting

### Build Failed
```bash
# Check logs di Render dashboard
# Common issues:
- Tesseract not found → Check Dockerfile apt-get install
- Python version mismatch → Specify in Dockerfile
- Missing dependencies → Update requirements.txt
```

### App Crashes
```bash
# Check runtime logs
# Common issues:
- Port binding → Gunicorn should bind to 0.0.0.0:$PORT
- Database connection → Check DATABASE_URL env var
- Tesseract path → Use default 'tesseract' on Linux
```

### OCR Not Working
```bash
# Verify Tesseract installation in container
# Check TESSDATA_PREFIX env variable
# Ensure language data (ind+eng) installed
```

## 📊 Monitoring

### Logs
- Access via Render dashboard
- Real-time streaming
- Search & filter

### Metrics
- CPU usage
- Memory usage
- Request count
- Response time

### Alerts (Paid Plans)
- Setup email/Slack notifications
- Monitor uptime
- Error tracking

## 🔄 Auto-Deploy

Render auto-deploys saat:
- Push ke `main` branch
- Manual trigger di dashboard

## 💰 Pricing

**Free Plan:**
- 750 hours/month
- Auto-sleep after 15min inactivity
- Slow cold start (~30s)
- 512MB RAM
- No persistent disk

**Starter Plan ($7/month):**
- No sleep
- Instant response
- 1GB RAM
- Persistent disk available

## 🎯 Production Checklist

- [ ] Update SECRET_KEY di environment variables
- [ ] Setup PostgreSQL database (recommended)
- [ ] Configure cloud storage untuk uploads
- [ ] Update Tesseract path untuk Linux
- [ ] Test all features setelah deploy
- [ ] Monitor error logs
- [ ] Setup health check endpoint
- [ ] Configure custom domain (optional)

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Community**: https://community.render.com
- **Status**: https://status.render.com

---

**Deployment Ready!** 🚀

URL akan tersedia di: `https://platform-detektor-plagiarisme.onrender.com`
