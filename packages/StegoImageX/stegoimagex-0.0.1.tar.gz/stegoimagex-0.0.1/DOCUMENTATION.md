# 📘 StegoImageX v11.0.0 — Dokumentasi Resmi

Advanced Adaptive AES-Encrypted Steganography Library for Python

> 📦 Dibuat oleh ATHALLAH RAJENDRA PUTRA JUNIARTO
> 🔒 Keamanan Data • 🧬 Intelejen Digital • ⚙️ Arsitektur Modular
> 📅 Rilis: Oktober 2025 | Versi: 0.0.1

---

## 🧠 Pendahuluan

**StegoImageX** adalah **perpustakaan Python untuk menyembunyikan pesan rahasia ke dalam gambar digital** menggunakan kombinasi berbagai metode keamanan modern:

- 🔐 **AES-256 CBC Encryption** untuk menjaga kerahasiaan pesan.
- 🧬 **SHA-256 Hash Integrity** untuk menjamin integritas pesan.
- 🧠 **Adaptive LSB Encoding** untuk efisiensi dan kamuflase alami.
- 🌀 **Dynamic Position Embedding (DPE)** berbasis password.
- ⚡ **Zlib Compression + Base64 Encoding** untuk efisiensi ruang.
- 🧩 **Batch Parallel Processing** untuk ribuan gambar sekaligus.
- 📈 **Bit Distribution Analysis Engine** untuk deteksi steganografi.

---

## 🧩 Konsep Dasar Steganografi

Steganografi digital adalah teknik menyembunyikan pesan dalam media seperti gambar, audio, atau video, tanpa menimbulkan perubahan visual signifikan.
StegoImageX berfokus pada gambar, dengan manipulasi bit LSB (Least Significant Bit).
Contoh sederhana (1 LSB):

| Warna Asli | Biner | Bit disisipkan | Hasil |
|----------|----------|----------|----------|
| R=11001000 | 11001000 | +1 → 11001001 | R=11001001 |
| G=10111100 | 10111100 | +0 → 10111100 | G=10111100 |
| B=11100011 | 11100011 | +1 → 11100011 | B=11100011 |

> Dengan mengganti bit terakhir, pesan disisipkan tanpa terlihat oleh mata manusia.

---

## ⚙️ Fitur-Fitur Utama

| Fitur | Deskripsi |
|----------|----------|
| **AES-256 CBC Encryption** | Enkripsi simetris 256-bit untuk menjaga kerahasiaan pesan. |
| **SHA-256 Integrity Verification** | Setiap pesan dilindungi dengan hash SHA-256. |
| **Dynamic Position Embedding (DPE)** | Urutan pixel embedding acak berdasarkan password. |
| **Adaptive LSB Encoding** | Jumlah bit disesuaikan dengan intensitas pixel (brighter = more bits). |
| **Compression Engine** | Zlib + Base64 memperkecil ukuran pesan. |
| **Batch Multithreading** | Proses paralel ribuan gambar secara efisien. |
| **Entropy-based Detection Engine** | Analisis statistik bit LSB untuk deteksi tersembunyi. |
| **Logging & Reporting** | Aktivitas disimpan otomatis di ``logs/`` dan hasil batch di ``.json`` / ``.csv``. |

---

## 🏗️ Arsitektur Sistem

```yaml
StegoImageX/
│
├── stegoimagex/
│ ├── init.py
│ ├── core.py
│ ├── batch.py
│ ├── encoder.py
│ ├── decoder.py
│ ├── detector.py
│ ├── compression.py
│ ├── crypto.py
│ ├── dpe.py
│ ├── integrity.py
│ ├── logger.py
│
├── setup.py
└── README.md
```

---

## 🔧 Modul dan Fungsi Internal

1️⃣ **core.py**
API utama yang menghubungkan seluruh sistem.
Fungsi Utama:

```python
hide_text(input_image, output_image, message, encrypted=False,
          password=None, layers=1, dynamic=True, compress=False,
          adaptive=True, logging=False)
```
> Menyembunyikan teks ke dalam gambar dengan enkripsi, kompresi, dan DPE.

```python
extract_text(image_path, password=None, layers=1,
             dynamic=True, compress=True, adaptive=True, logging=False)
```
> Mengekstrak pesan dari gambar.

```python
detect_message_info(image_path, logging=False, layers=1)
```
> Menganalisis probabilitas keberadaan pesan.

2️⃣ **encoder.py**
Melakukan embedding bit pesan ke dalam pixel RGB.

**Proses utama:**
1. Kompresi pesan → zlib + base64
2. Tambahkan hash → ``[HASH]...[/HASH]``
3. Enkripsi (jika aktif) → AES-256 CBC
4. Tandai mode adaptif ``[ADP]`` atau ``[NOADP]``
5. Konversi ke bit string
6. Sisipkan ke gambar melalui Adaptive LSB
7. Simpan hasil ke file baru

**Algoritma Adaptive LSB:**
| Intensitas Pixel | Bit yang digunakan |
|----------|----------|
| >180 (terang) | 4 bit |
| 100–180 | 3 bit |
| 50–100 | 2 bit |
| <50 (gelap) | 1 bit |

3️⃣ **decoder.py**
Melakukan ekstraksi bit dari gambar.

**Langkah:**
1. Baca pixel RGB
2. Kumpulkan bit sesuai LSB
3. Gabungkan menjadi teks ASCII
4. Deteksi tag ``[ADP]``, ``[ENC]``, ``[CMP]``, dll
5. Dekripsi jika terenkripsi
6. Dekompresi jika terkompresi
7. Verifikasi hash integritas

4️⃣ **crypto.py**
Modul enkripsi AES-256 CBC menggunakan PyCryptodome.

```python
encrypt_message(message: str, password: str) -> str
decrypt_message(encrypted_message: str, password: str) -> str
```

- Derivasi key: SHA-256(password)
- IV acak disimpan di awal ciphertext
- Padding: PKCS7

5️⃣ **compression.py**
Kompresi pesan agar efisien:

```python
compress_message("teks")
decompress_message("encoded_data")
```

Menggunakan kombinasi zlib + base64 agar dapat disimpan aman di dalam bit.

6️⃣ **dpe.py**
Dynamic Position Embedding (DPE) menghasilkan urutan acak deterministik dari hash password.

```python
generate_dpe_positions(width, height, password)
```

> Posisi pixel embedding selalu sama untuk password dan ukuran gambar yang sama.

7️⃣ **integrity.py**
Sistem hash integritas pesan:
- Tag: ``[HASH]<digest>[/HASH]<message>``
- Hashing: **SHA-256**
- Fungsi utama:
    1. ``compute_hash()``
    2. ``embed_hash()``
    3. ``extract_and_verify_hash()``

8️⃣ **detector.py**
Analisis statistik LSB.

Mengukur:
- Entropy
- Bit ratio (0:1)
- Randomness score
- Probability detection

```python
detect_message(image_path, layers=2)
```

> Mengembalikan ``dict`` hasil analisis probabilistik.

9️⃣ **batch.py**
Pemrosesan banyak gambar sekaligus dengan **ThreadPoolExecutor**.

Fungsi utama:
- ``batch_hide_text()``
- ``batch_extract_text()``
- ``batch_detect_messages()``

Dapat dijalankan pada 4–16 thread secara paralel.

🔟 **logger.py**
Sistem pencatatan otomatis:
- Format log:
```log
[YYYY-MM-DD HH:MM:SS] [ACTION] detail
```
- Direktori: ``logs/``
- Dukungan ekspor:
    1. ``.json``
    2. ``.csv``

---

## 🧮 Algoritma Teknis

🔹 **Terminator Bit**

Bit terakhir pesan: **11111110**.
Menandai akhir payload agar decoding berhenti tepat waktu.

🔹 **Format Payload**

```css
[ADP][ENC][HASH]<digest>[/HASH][CMP]BASE64DATA
```

🔹 **Probability Detection Formula**

```python
probability = round((1 - abs(0.5 - ratio)) * 100, 2)
```
Semakin mendekati 0.5 distribusi bit, semakin tinggi kemungkinan ada pesan tersembunyi.

---

## ⚙️ Parameter & Opsi Penggunaan

| Parameter | Jenis | Default | Deskripsi |
|----------|----------|----------|
| ``input_image`` | str | — | Path gambar sumber |
| ``output_image`` | str | — | Path untuk menyimpan hasil |
| ``message`` | str | — | Pesan teks yang akan disembunyikan |
| ``encrypted`` | bool | False | Aktifkan enkripsi AES-256 |
| ``password`` | str | None | Password untuk enkripsi/dekripsi |
| ``layers`` | int | 1 | Jumlah bit LSB yang digunakan (1–4) |
| ``dynamic`` | bool | True | Aktifkan DPE (Dynamic Position Embedding) |
| ``compress`` | bool | False | Aktifkan kompresi zlib |
| ``adaptive`` | bool | True | Gunakan Adaptive LSB |
| ``logging`` | bool | False | Simpan log aktivitas ke file |

---

## 🧵 Batch Processing

| Fitur | Deskripsi |
|----------|----------|
| ``hide_text_batch()`` | Menyembunyikan pesan ke semua gambar di folder. |
| ``extract_text_batch()`` | Mengekstrak semua pesan dari folder. |
| ``detect_message_batch()`` | Menganalisis probabilitas semua gambar di folder. |

Output dapat disimpan sebagai:
- ``report.json``
- ``report.csv``

---

## 🧾 Logging & Pelaporan
Setiap aktivitas (HIDE, EXTRACT, DETECT) disimpan di:

```bash
logs/stegoimagex_YYYYMMDD.log
```

Contoh isi:

```log
[2025-10-22 12:45:10] [HIDE] input.png -> output.png | enc=True | cmp=True | dyn=True
[2025-10-22 12:45:15] [EXTRACT] output.png | len=128 | cmp=True
```

---

## 🔍 Analisis Deteksi Pesan
Output ``detect_message_info()``:

```python
{
  "has_marker": True,
  "entropy": 0.9972,
  "bit_ratio": 0.4986,
  "randomness_score": 0.0014,
  "probability_of_hidden_message": 96.52,
  "message_detected": True
}
```

Interpretasi:
- **Entropy ~1.0** → bit acak → kemungkinan pesan tinggi
- **Ratio ~0.5** → distribusi seimbang → kemungkinan pesan tinggi
- **Marker ditemukan (11111110)** → pesan pasti ada

---

## ⚡ Kinerja & Optimasi

| Teknik | Dampak |
|----------|----------|
| Adaptive LSB | Mengurangi distorsi visual |
| Kompresi | Mempercepat embedding |
| DPE | Menghindari deteksi forensik |
| Multithreading | 3–5× lebih cepat di batch mode |
| Logging asynchronous | Tidak menghambat proses utama |

---

## 💡 Contoh Implementasi Lengkap

```python
from stegoimagex import hide_text, extract_text, detect_message_info

# 1️⃣ Sembunyikan pesan
hide_text(
    "input.png", "secret.png",
    message="Halo dunia tersembunyi!",
    encrypted=True, password="12345",
    compress=True, adaptive=True, logging=True
)

# 2️⃣ Ekstrak pesan
msg = extract_text("secret.png", password="12345")
print("Pesan:", msg)

# 3️⃣ Deteksi pesan
info = detect_message_info("secret.png")
print("Analisis:", info)
```

---

## 🧩 Struktur Direktori & Instalasi

Menggunakan Github(Lokal):

```bash
git clone https://github.com/Athallah1234/StegoImageX.git
cd StegoImageX
pip install -e .
```

Menggunakan pip:

```pip
pip install stegoimagex
```

Dependensi:

```shell
Pillow>=9.0.0
pycryptodome>=3.10.0
```

---

## 🪪 Lisensi & Hak Cipta

Lisensi: **[MIT License]()**.
Hak Cipta © 2025 — **[ATHALLAH RAJENDRA PUTRA JUNIARTO]()**.
> Penggunaan bebas untuk keperluan akademik, penelitian, dan pengembangan open-source.
> Dilarang digunakan untuk penyembunyian data ilegal atau pelanggaran privasi.