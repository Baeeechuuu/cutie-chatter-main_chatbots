 # CutieChatter Desktop 💬🖥️

Aplikasi chatbot desktop berbasis PyQt6 dengan AI DeepSeek-R1 untuk Windows. Chat dengan AI yang cerdas menggunakan antarmuka desktop yang modern dan responsif.

## 🎯 Fitur Utama

- 🖥️ **Aplikasi Desktop Native** - Berjalan langsung di Windows
- 🤖 **AI DeepSeek-R1** - Model AI canggih untuk percakapan natural
- 💭 **Sentiment Analysis** - Analisis emosi dan sentimen dalam percakapan
- 👤 **User Authentication** - Sistem login dan registrasi pengguna
- 💾 **Chat History** - Penyimpanan riwayat percakapan
- 🎨 **Interface Modern** - Antarmuka web hybrid dalam aplikasi desktop
- 📁 **OCR Support** - Baca teks dari gambar dan dokumen (opsional)
- 🔊 **TTS Support** - Text-to-Speech (opsional)

## 📋 Persyaratan Sistem

### Sistem Operasi
- **Windows 10** atau yang lebih baru (64-bit)
- RAM minimum: **8GB** (16GB direkomendasikan)
- Storage: **5GB** ruang kosong

### Software yang Diperlukan
- **Python 3.8+** (Python 3.10-3.11 direkomendasikan)
- **Ollama** - Server AI lokal
- **Git** (untuk clone repository)

## 🚀 Panduan Instalasi Lengkap

### Langkah 1: Install Python

1. Download Python dari [python.org](https://www.python.org/downloads/)
2. **PENTING**: Centang "Add Python to PATH" saat instalasi
3. Verifikasi instalasi:
```bash
python --version
pip --version
```

### Langkah 2: Install Ollama

1. Download Ollama untuk Windows dari [ollama.ai](https://ollama.ai/)
2. Install Ollama
3. Buka Command Prompt dan jalankan:
```bash
# Start Ollama server
ollama serve

# Di terminal baru, download model DeepSeek-R1
ollama pull deepseek-r1:1.5b
```

**CATATAN**: Download model akan memakan waktu dan bandwidth yang cukup besar (sekitar 1-2GB).

### Langkah 3: Clone dan Setup Aplikasi

1. Clone repository:
```bash
git clone <repository-url>
cd cutie-chatter-main_chatbots
```

2. Buat virtual environment (direkomendasikan):
```bash
python -m venv cutie_env
cutie_env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Langkah 4: Setup Database (Opsional)

Jika ingin menggunakan fitur autentikasi dan penyimpanan chat:

1. Buat file `.env`:
```bash
# Database Configuration (Opsional - jika tidak ada akan menggunakan SQLite lokal)
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=cutiechatter
DB_USER=your-username
DB_PASSWORD=your-password
DB_SSLMODE=prefer
```

2. Setup database:
```bash
python setup_supabase.py
```

## 🏃‍♂️ Cara Menjalankan Aplikasi

### Metode 1: Jalankan Langsung dari Python

1. **Pastikan Ollama berjalan:**
```bash
# Di Command Prompt, jalankan:
ollama serve
```

2. **Jalankan aplikasi:**
```bash
# Di terminal/cmd yang berbeda, dari folder aplikasi:
python run.py
```

### Metode 2: Jalankan dengan Opsi Advanced

```bash
# Jalankan dengan model specific
python cutie.py --model deepseek-r1:1.5b

# Jalankan tanpa authentication
python cutie.py --no-auth

# Jalankan dalam guest mode
python cutie.py --guest
```

### Metode 3: Build Executable (Distribusi)

Untuk membuat file .exe yang bisa dijalankan tanpa Python:

```bash
# Install PyInstaller (sudah ada di requirements.txt)
pip install pyinstaller

# Build executable
pyinstaller CutieChatbot.spec

# File .exe akan ada di folder dist/
```

## 🔧 Konfigurasi dan Troubleshooting

### Mengatur Model AI

Model default adalah `deepseek-r1:1.5b`. Untuk menggunakan model lain:

```bash
# Download model lain (opsional)
ollama pull deepseek-r1:7b    # Model lebih besar, lebih pintar
ollama pull llama2           # Alternatif model
ollama pull mistral          # Model lain

# Jalankan dengan model specific
python run.py --model deepseek-r1:7b

### Masalah Umum dan Solusi

#### ❌ "Ollama server connection failed"
**Solusi:**
```bash
# 1. Pastikan Ollama terinstall
ollama --version

# 2. Start Ollama server
ollama serve

# 3. Test koneksi
ollama list
```

#### ❌ "No DeepSeek models found"
**Solusi:**
```bash
# Download model yang diperlukan
ollama pull deepseek-r1:1.5b
```

#### ❌ "Module 'PyQt6' not found"
**Solusi:**
```bash
# Install ulang dependencies
pip install --upgrade -r requirements.txt

# Atau install manual
pip install PyQt6 PyQt6-WebEngine
```

#### ❌ "Error starting application"
**Solusi:**
```bash
# Jalankan dengan verbose output
python cutie.py --no-auth

# Check log error di console
```

#### ❌ Aplikasi lambat/hang
**Solusi:**
- Pastikan RAM minimal 8GB
- Gunakan model yang lebih kecil: `deepseek-r1:1.5b`
- Tutup aplikasi lain yang berat

### Optimasi Performa

1. **Untuk PC dengan RAM terbatas:**
```bash
# Gunakan model kecil
python run.py --model deepseek-r1:1.5b
```

2. **Untuk PC dengan RAM besar (16GB+):**
```bash
# Gunakan model besar untuk hasil lebih baik
ollama pull deepseek-r1:7b
python run.py --model deepseek-r1:7b
```

3. **Monitoring resource:**
- Buka Task Manager untuk monitor penggunaan RAM/CPU
- Ollama biasanya menggunakan 2-8GB RAM tergantung model

## 📁 Struktur Aplikasi

```
CUTIE-CHATTER-MAIN_CHATBOTS/
├── __pycache__/              # Python cache files
├── analysis/                 # Data analysis modules
├── background/               # Background processing
├── build/                    # Built application files
├── dist/                     # Distribution files
├── icons/                    # Application icons
├── model_checkpoints/        # AI model checkpoints
├── ocr/                      # OCR processing modules
├── pre-prod/                 # Pre-production files
├── sentiment/                # Sentiment analysis
├── stt/                      # Speech-to-Text modules
├── temp_audio/               # Temporary audio files
├── themes/                   # UI themes
├── training_logs/            # Model training logs
├── tts/                      # Text-to-Speech modules
├── web_ui/                   # Web interface files
├── auth_bridge.py            # Authentication bridge
├── auth_postgresql.py        # PostgreSQL authentication
├── auth.html                 # Authentication page
├── auth.py                   # Main authentication module
├── backend2.py               # Secondary backend
├── backends.py               # Backend configurations
├── chat_bridge.py            # Chat bridge module
├── cutie.py                  # Main application entry point
├── CutieChatbot.spec         # PyInstaller specification
├── cutiechatter_users.db     # User database
├── database_config.py        # Database configuration
├── dataset_patch.py          # Dataset patching utilities
├── demo_output.wav           # Demo audio file
├── demo_tts.py               # TTS demonstration
├── generate_dummy_data.py    # Test data generation
├── migration_guide.md        # Database migration guide
├── readme.md                 # This file
├── requirements.txt          # Python dependencies
├── run.py                    # Application runner
├── setup_supabase.py         # Supabase setup
├── SUPABASE_MIGRATION_GUIDE.md # Supabase migration guide
├── tempCodeRunnerFile.py     # Temporary code files
├── test_postgresql_setup.py  # PostgreSQL testing
├── test_supabase_connection.py # Supabase testing
├── tts_training.log          # TTS training logs
├── ui_chatbot.html           # Main chat interface
└── windows_patch.py          # Windows compatibility patch
```

## 💡 Tips Penggunaan

### 1. First Time Setup
- Pastikan internet stabil untuk download model AI
- Download model bisa memakan waktu 10-30 menit
- Model akan disimpan permanent di sistem

### 2. Daily Usage
- Selalu jalankan `ollama serve` sebelum buka aplikasi
- Aplikasi bisa diminimize ke system tray
- Chat history tersimpan otomatis

### 3. Advanced Features
- **Sentiment Analysis**: Otomatis analisis emosi dalam chat
- **OCR**: Drag & drop gambar untuk ekstrak teks
- **Theme**: Bisa ganti tema dark/light
- **Export Chat**: Save percakapan ke file

## 📖 Panduan Step-by-Step untuk Pemula

### Setup Pertama Kali (Detail)

1. **Buka Command Prompt sebagai Administrator:**
   - Tekan `Win + R`
   - Ketik `cmd`
   - Tekan `Ctrl + Shift + Enter`

2. **Install Ollama:**
   ```bash
   # Download dan install dari https://ollama.ai/
   # Atau gunakan winget jika tersedia
   winget install Ollama.Ollama
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   ```
   - **JANGAN TUTUP** window ini, biarkan terus berjalan

4. **Buka Command Prompt baru:**
   ```bash
   # Download model AI (ini akan lama, sabar)
   ollama pull deepseek-r1:1.5b
   
   # Verify model terdownload
   ollama list
   ```

5. **Clone aplikasi:**
   ```bash
   # Pindah ke folder yang diinginkan
   cd C:\Users\%USERNAME%\Desktop
   
   # Clone repository (ganti <repository-url> dengan URL asli)
   git clone <repository-url>
   cd cutie-chatter-main_chatbots
   ```

6. **Setup Python environment:**
   ```bash
   # Buat virtual environment
   python -m venv cutie_env
   
   # Activate environment
   cutie_env\Scripts\activate
   
   # Install requirements
   pip install -r requirements.txt
   ```

7. **Test run aplikasi:**
   ```bash
   # Pastikan masih di folder aplikasi dan venv aktif
   python run.py
   ```

### Penggunaan Harian

1. **Setiap mau pakai aplikasi:**
   ```bash
   # 1. Start Ollama (jika belum jalan)
   ollama serve
   
   # 2. Di Command Prompt baru, masuk ke folder app
   cd C:\Users\%USERNAME%\Desktop\cutie-chatter-main_chatbots
   
   # 3. Activate virtual environment
   cutie_env\Scripts\activate
   
   # 4. Jalankan aplikasi
   python run.py
   ```

2. **Shortcut (Buat file .bat):**
   
   Buat file `start_cutie.bat` di folder aplikasi:
   ```batch
   @echo off
   cd /d "C:\Users\%USERNAME%\Desktop\cutie-chatter-main_chatbots"
   call cutie_env\Scripts\activate
   python run.py
   pause
   ```
   
   Double-click file `.bat` ini untuk langsung jalankan aplikasi.

## 🔍 Monitoring dan Debugging

### Check Status System

```bash
# Check Python
python --version

# Check Ollama
ollama --version
ollama list

# Check dependencies
pip list | findstr PyQt6
pip list | findstr ollama
```

### Log Aplikasi

Aplikasi akan menampilkan log di console. Perhatikan pesan:
- ✅ = Sukses
- ❌ = Error
- ⚠️ = Warning

Common log messages:
```
✅ Ollama server running!
✅ DeepSeek models found: ['deepseek-r1:1.5b']
🚀 CutieChatter started with model: deepseek-r1:1.5b
❌ Ollama server connection failed
❌ No DeepSeek models found!
```

## 🎯 FAQ (Frequently Asked Questions)

### Q: Kenapa aplikasi tidak bisa connect ke Ollama?
A: Pastikan `ollama serve` sudah dijalankan dan tidak ada error. Check dengan `ollama list`.

### Q: Model mana yang paling baik?
A: 
- `deepseek-r1:1.5b` - Ringan, cocok untuk PC 8GB RAM
- `deepseek-r1:7b` - Lebih pintar, butuh 16GB+ RAM
- `deepseek-r1:14b` - Paling pintar, butuh 32GB+ RAM

### Q: Bisa jalankan tanpa internet?
A: Setelah model didownload, aplikasi bisa jalan offline. Tapi download pertama butuh internet.

### Q: Aman tidak data chatnya?
A: Semua data disimpan lokal di PC Anda. Tidak ada yang dikirim ke server luar.

### Q: Bisa ubah tema UI?
A: Ya, ada toggle dark/light mode di aplikasi.

### Q: Bisa export chat history?
A: Fitur export sedang dikembangkan. Saat ini data tersimpan di database lokal.

## 📞 Support dan Kontribusi

### Jika Ada Masalah:
1. Check console/terminal untuk pesan error
2. Pastikan semua dependencies terinstall dengan benar
3. Verify Ollama server berjalan dengan `ollama list`
4. Restart aplikasi dan Ollama server
5. Buat issue di GitHub dengan detail error

### Kontribusi:
- Fork repository ini
- Buat branch untuk fitur baru
- Submit pull request dengan deskripsi jelas

### Contact:
- GitHub Issues untuk bug reports
- Discussion untuk feature requests

## 📄 Lisensi

Proyek ini menggunakan lisensi MIT. Lihat file LICENSE untuk detail lengkap.

---

**🎉 Selamat Menggunakan CutieChatter Desktop!**

Untuk pertanyaan atau bantuan lebih lanjut, silakan buka issue di GitHub repository ini atau hubungi developer melalui email yang tertera di profil GitHub.

**Happy Chatting! 💬✨**
