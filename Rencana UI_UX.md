# **📝 Dokumen Spesifikasi UI/UX & Integrasi API — FootFit**

**Deskripsi Aplikasi:** Web app sederhana tanpa *login* untuk mengukur dimensi panjang dan lebar kaki secara presisi menggunakan foto kamera HP dengan objek referensi kartu (KTP/ATM/SIM)

## ---

**🗺️ Arsitektur Alur Pengguna (User Flow)**

Aplikasi akan dibagi menjadi **4 Halaman/State Utama**:

\[Halaman 1: Panduan\] ➔ \[Halaman 2: Kamera/Upload\] ➔ \[Halaman 3: Loading\] ➔ \[Halaman 4: Hasil\]

## **🧱 Detail Spesifikasi Per Halaman**

### **Halaman 1: Panduan Pengambilan Foto (Landing Page)**

* **Tujuan:** Memastikan pengguna mengambil foto dengan standar yang benar agar algoritma backend menghasilkan data akurat \[cite: 2026-03-26\].  
* **Komponen UI:**  
  * Tombol utama: "Mulai Ukur Kaki" (Langsung menuju Halaman 2).  
  * **Infografis Visual (WAJIB):** Tim frontend diharapkan membagi panduan ini menjadi ilustrasi visual (Kartu Hijau untuk BENAR, Kartu Merah untuk SALAH):  
    * ✅ **HARUS:** Tumit kaki menempel dinding (jangan ditekan berlebihan).  
    * ✅ **HARUS:** Kartu diletakkan di samping kaki (beri sedikit jarak)\].  
    * ✅ **HARUS:** Posisi kartu tegak lurus sempurna (bisa vertikal atau horizontal).  
    * ✅ **HARUS:** Posisi kaki lurus sejajar dinding.  
    * ❌ **JANGAN:** Betis menutupi batas/garis antara lantai dan dinding.  
    * ❌ **JANGAN:** Menggunakan kartu yang warnanya mirip atau menyatu dengan warna lantai.  
    * ❌ **JANGAN:** Kartu ditaruh terlalu maju melewati ujung jari kaki.  
    * ❌ **JANGAN:** Meletakkan kartu miring/diagonal.  
    * ❌ **JANGAN:** Mengambil foto dengan sudut kamera yang terlalu condong/miring.  
    * 💡 *Tips Tambahan:* Pengguna disarankan meletakkan HP di atas paha saat membidik foto dan wajib mengaktifkan lampu kilat (*flash*) kamera.

### **Halaman 2: Kamera / Unggah Gambar**

* **Tujuan:** Menangkap atau menerima file gambar dari pengguna  
* **Komponen UI:**  
  * Dua opsi input: "Ambil Foto" (membuka kamera HP) atau "Pilih dari Galeri"   
  * **UI Overlay (Garis Pemandu Kamera):** Saat kamera aktif, tampilkan siluet samar berbentuk kaki dan kotak kartu di layar. Ini membantu pengguna memosisikan kamera secara tegak lurus di atas objek.

### **Halaman 3: Loading State (Proses Validasi)**

* **Tujuan:** Menahan pengguna agar tidak menutup aplikasi selama backend memproses gambar.  
* **Komponen UI:**  
  * Animasi *loading* interaktif (misal: efek laser *scanning* atau transisi memindai kaki) .  
  * Teks dinamis yang berganti setiap 2 detik untuk edukasi, seperti:  
    * *"Mencari objek kartu referensi..."*  
    * *"Memisahkan objek kaki dari latar belakang..."*   
    * *"Menghitung dimensi dalam satuan milimeter..."*

### **Halaman 4: Dashboard Hasil Pengukuran**

* **Tujuan:** Menampilkan hasil analisis secara transparan dan solutif  
* **Komponen UI (Dibagi menjadi 3 Card Utama):**  
  1. **Card 1: Bukti Transparansi (Foto Hasil)**  
     * Menampilkan gambar hasil pemrosesan dari backend (image\_base64). Gambar ini otomatis memperlihatkan garis penanda jangka sorong (caliper kuning) dan deteksi dinding (merah) agar pengguna tahu proses pengukuran berjalan objektif   
  2. **Card 2: Angka Dimensi & Morfologi**  
     * Menampilkan data length\_mm dan width\_mm (Frontend silakan konversi ke satuan cm dengan membagi angka tersebut dengan 10 agar lebih familier bagi pengguna awam)  
     * **Logika Status Tipe Kaki (Frontend Level):**  
       * Jika variabel ratio dari backend **\> 0.42**, tampilkan label tebal berwarna jingga/merah: 🔴 **WIDE-FIT (Kaki Lebar)**  
       * Jika variabel ratio **≤ 0.42**, tampilkan label berwarna hijau: 🟢 **STANDARD-FIT (Kaki Normal)**  
  3. **Card 3: Rekomendasi Ukuran Sepatu**  
     * Menampilkan konversi ukuran sepatu berdasarkan panjang kaki (length\_mm)   
     * *Catatan untuk Frontend:* Silakan gunakan standardisasi *Size Chart* internasional (EU/US/UK) yang sesuai, atau sediakan fitur pencocokan ukuran berdasarkan tabel merek sepatu tertentu

## ---

**🛠️ Kontak Informasi API Backend (Untuk Frontend)**

* Di folder utama, saya sudah buat fungsi clean bernama `process_foot_measurement(image_path)` di file `main.py` yang siap dipanggil . Fungsi itu menerima path file gambar dan langsung mengembalikan output Dictionary (JSON-ready) berupa panjang, lebar, rasio, dan gambar hasil dalam bentuk Base64

* Silakan cek repositori GitHub. Kalian bebas mau membungkus fungsi Python tersebut menggunakan framework API pilihan kalian (misal: FastAPI, Flask, atau menggunakan Node.js child-process jika mau)

### **Format Respon JSON dari Backend (Jika Sukses):**

JSON

{  
  "status": "success",  
  "data": {  
    "length\_mm": 265.40,  
    "width\_mm": 114.12,  
    "ratio": 0.43,  
    "image\_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD..."  
  }  
}

### **Format Respon JSON (Jika Gagal):**

Frontend diharapkan menampilkan pesan eror yang sesuai di layar jika menerima skenario gagal berikut \[cite: 2026-03-26\]:

JSON

{  
  "status": "error",  
  "message": "Gagal mendeteksi kartu referensi. Pastikan kartu terlihat jelas dan ulangi foto."  
}

