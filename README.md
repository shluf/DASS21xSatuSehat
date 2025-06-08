# API Middleware DASS-21 & SATUSEHAT

## Gambaran Umum
Middleware ini berfungsi sebagai jembatan antara sistem asesmen psikologis [DASS-21](https://github.com/shluf/dass21-be) dan platform [SATUSEHAT](https://satusehat.kemkes.go.id/platform/docs/id/playbook/) dari Kementerian Kesehatan. Dibangun menggunakan **FastAPI**, API ini menyediakan serangkaian endpoint untuk mengelola pengguna, memproses hasil tes DASS-21 untuk memberikan saran kesehatan mental, dan berinteraksi dengan API FHIR SATUSEHAT untuk manajemen data pasien.

## Fitur Utama
*   **Proses DASS-21**: Menerima skor dari 21 pertanyaan DASS, mengklasifikasikan tingkat depresi, kecemasan, dan stres, lalu memberikan saran tindak lanjut yang relevan.
*   **Manajemen Pasien (SATUSEHAT)**: Terintegrasi dengan SATUSEHAT untuk mendaftarkan pasien baru, mencari data pasien berdasarkan NIK, mendapatkan daftar lokasi fasilitas kesehatan, dan membuat data kunjungan (Encounter).
*   **Otentikasi Pengguna**: Menggunakan JWT (JSON Web Tokens) untuk mengamankan endpoint dan memastikan bahwa hanya pengguna terdaftar yang dapat mengakses data sensitif.

## Struktur Proyek
Kode diatur secara modular untuk kemudahan pemeliharaan. Berikut adalah rincian struktur direktori utama:

| Direktori        | Deskripsi                                                                                  |
|------------------|--------------------------------------------------------------------------------------------|
| `src/`           | Direktori utama yang berisi semua logika aplikasi.                                         |
| `src/api/`       | Mengatur *endpoint* API berdasarkan grup fungsionalitas (`auth`, `dass`, `patient`).       |
| `src/services/`  | Logika bisnis inti, seperti `inference.py` untuk pemrosesan asesmen DASS-21.               |
| `src/clients/`   | Komunikasi dengan API eksternal, seperti `satusehat_client.py` untuk interaksi SATUSEHAT. |
| `src/models/`    | Definisi model data Pydantic untuk validasi dan skema database.                            |
| `src/core/`      | Konfigurasi aplikasi (`config.py`) dan manajemen keamanan (`security.py`).                 |
| `src/db.py`      | Konfigurasi dan inisialisasi koneksi database.                                             |
| `main.py`        | Titik masuk utama aplikasi FastAPI.                                                        |

---

## Endpoint API

Berikut adalah daftar endpoint yang tersedia, dikelompokkan berdasarkan fungsionalitasnya.

#### 1. Otentikasi (`/api/auth`)
*   `POST /api/auth/register` - Mendaftarkan pengguna baru beserta detail data pasien. (Otentikasi: Tidak diperlukan)
*   `POST /api/auth/login` - Login untuk pengguna yang sudah ada dan mendapatkan access token. (Otentikasi: Tidak diperlukan)
*   `GET /api/auth/user` - Mendapatkan detail pengguna yang sedang login. (Otentikasi: Diperlukan)

#### 2. Asesmen DASS-21 (`/api`)
*   `POST /api/dass21` - Mengirimkan skor DASS-21 untuk diproses. Mengembalikan level kondisi (misal: "normal", "sedang") beserta pesan dan saran detail. (Otentikasi: Diperlukan)

#### 3. Manajemen Pasien & Kunjungan (`/api`)
*   `POST /api/register-patient` - Mencari atau mendaftarkan pasien baru di SATUSEHAT menggunakan NIK. (Otentikasi: Diperlukan)
*   `GET /api/locations` - Mendapatkan daftar semua lokasi (poli, ruangan) yang terdaftar di SATUSEHAT untuk sebuah organisasi. (Otentikasi: Diperlukan)
*   `POST /api/create-visit` - Membuat data kunjungan (Encounter) baru di SATUSEHAT untuk pasien yang sudah terdaftar. (Otentikasi: Diperlukan)

---

## Langkah-langkah Menjalankan Middleware

Berikut adalah panduan untuk menyiapkan dan menjalankan server middleware di lingkungan lokal.

**1. Prasyarat**
*   Pastikan **Python 3.8+** dan `pip` terinstal di sistem Anda.

**2. Setup Lingkungan & Instalasi**

   A. **Buat dan Aktifkan Lingkungan Virtual (`venv`)**
   
   Sangat disarankan untuk menggunakan lingkungan virtual untuk mengisolasi dependensi proyek. Buka terminal di direktori root proyek dan jalankan perintah berikut:

   1. Buat lingkungan virtual bernama 'venv'
   ```bash
   python -m venv venv
   ```

   2. Aktifkan lingkungan virtual
   - Untuk Windows (PowerShell/CMD):
   ```bash
   .\venv\Scripts\Activate
   ```
   
   - Untuk macOS/Linux (Bash):
   ```bash
   source venv/bin/activate
   ```
   Setelah diaktifkan, Anda akan melihat `(venv)` di awal baris terminal Anda.

   B. **Instal Dependensi**
   
   Dengan lingkungan virtual yang aktif, instal semua paket yang diperlukan menggunakan file `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

**3. Konfigurasi Environment**
   Buat file bernama `.env` di direktori root proyek. File ini akan berisi semua kredensial dan konfigurasi yang sensitif. Salin dan isi nilai-nilai berikut:

   ```env
   # Konfigurasi SATUSEHAT
   AUTH_URL=https://api-satusehat-stg.dto.kemkes.go.id/oauth2/v1
   BASE_URL=https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1
   CLIENT_ID=YOUR_SATUSEHAT_CLIENT_ID
   CLIENT_SECRET=YOUR_SATUSEHAT_CLIENT_SECRET
   ORGANIZATION_ID=YOUR_ORGANIZATION_ID_SATUSEHAT
   PRACTITIONER_ID=YOUR_DEFAULT_PRACTITIONER_ID

   # Konfigurasi JWT untuk otentikasi
   JWT_SECRET_KEY=SECRET_KEY_UNTUK_ENKRIPSI_TOKEN_ANDA
   JWT_ALGORITHM=HS256
   ```
   Untuk mendapatkan CLIENT_ID, CLIENT_SECRET, dan ORGANIZATION_ID dapat dilakukan dengan membuat akun di laman [Satu sehat](https://satusehat.kemkes.go.id/platform/login), untuk lebih lengkapnya dapat dilihat di [Panduan Daftar Akun Satu Sehat](https://satusehat.kemkes.go.id/platform/docs/id/registration-guide/registration/#registration). 

**4. Jalankan Server**
   Setelah semua dependensi terinstal dan file `.env` terkonfigurasi, jalankan server menggunakan Uvicorn dari direktori root:
   ```bash
   uvicorn main:app --reload
   ```
*   `main`: Merujuk ke file `main.py`.
*   `app`: Merujuk ke objek `FastAPI` yang dibuat di dalam `main.py`.
*   `--reload`: Flag ini akan membuat server otomatis restart setiap kali ada perubahan pada kode.

Server API sekarang akan berjalan dan dapat diakses di **http://localhost:8000**. Anda bisa mulai menguji endpoint menggunakan Postman atau alat sejenisnya. 

## Dokumentasi Postman
   Untuk dokumentasi API nya dapat diakses melalui link berikut https://documenter.getpostman.com/view/37974053/2sB2x3nDD7
