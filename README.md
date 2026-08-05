# Analisis Jejaring Sosial — Organisasi Kemahasiswaan

Proyek tugas mata kuliah **Analisis Jejaring Sosial (SNA)** yang mengevaluasi efektivitas
komunikasi dalam organisasi kemahasiswaan menggunakan pendekatan *Social Network Analysis*
(Python/NetworkX, diekspor ke Gephi).

## 1. Deskripsi Proyek
Studi ini memodelkan jejaring komunikasi sebuah organisasi kemahasiswaan (≥1.000 anggota)
sebagai graf tak berarah berbobot, lalu menganalisis:
- Sentralitas aktor (degree, betweenness, closeness, eigenvector)
- Karakteristik struktural global (density, diameter, average path length, clustering)
- Deteksi komunitas (algoritma Louvain)
- Simulasi propagasi informasi (model epidemi SIR)

## 2. Dataset & Sumbernya
Data riil komunikasi organisasi kemahasiswaan (log rapat/WA grup) sulit diperoleh dan berisiko
etis (privasi anggota) untuk dipublikasikan di repository publik. Karena itu proyek ini
menggunakan **graf sintetis yang dibangkitkan dengan model realistis**
(`nx.powerlaw_cluster_graph`, N=1200, m=3, p=0.15) yang menghasilkan struktur *scale-free* dan
*small-world* — pola yang secara empiris juga muncul pada jejaring sosial/organisasi nyata
(lih. Newman, 2018; Wasserman & Faust, 1994). Atribut naratif (nama fiktif, peran struktural,
divisi) dipasangkan ke node berdasarkan peringkat sentralitas dan hasil deteksi komunitas,
sehingga graf dapat dinarasikan secara konsisten sebagai representasi organisasi kemahasiswaan.

Alternatif dataset publik riil untuk pengembangan lebih lanjut: [SNAP Stanford](https://snap.stanford.edu/data/).

## 3. Cara Menjalankan
```bash
pip install -r requirements.txt
python src/sna_pipeline.py
```
Output tersimpan otomatis ke `visualisasi/` (grafik PNG) dan `data/` (GEXF + ringkasan JSON).

## 4. Struktur Folder
```
Analisis-Jejaring-Sosial/
├── data/               # graf hasil (GEXF utk Gephi) + ringkasan metrik (JSON)
├── src/                # kode Python (NetworkX) — pipeline analisis lengkap
├── visualisasi/         # grafik: distribusi degree, top-10 sentralitas, jejaring, SIR
├── laporan/             # laporan akhir (buku digital, .docx/.pdf)
├── requirements.txt
└── README.md
```

## 5. Ringkasan Hasil
| Metrik | Nilai |
|---|---|
| Jumlah node | 1.200 |
| Jumlah edge | 3.590 |
| Rata-rata degree | 5,98 |
| Density | 0,0050 |
| Diameter (largest component) | 6 |
| Average path length | 3,56 |
| Average clustering coefficient | 0,100 |
| Jumlah komunitas (Louvain) | 29 |
| Modularitas (Q) | 0,643 |

Aktor kunci teratas (gabungan degree/betweenness/eigenvector): **Indah Kusuma (Ketua Umum)**,
**Putri Utami (Sekretaris Umum)**, **Teguh Lestari (Bendahara Umum)** — konsisten muncul tinggi
di beberapa metrik sekaligus, mengindikasikan risiko *single point of failure* komunikasi.

Simulasi SIR menunjukkan penyebaran informasi dari node kunci (Ketua Umum) mencapai puncak lebih
cepat (t=16) dan lebih tinggi dibanding dari anggota berdegree rendah (t=27), mendukung strategi
*influencer maximization* untuk diseminasi pengumuman penting.

## 6. Laporan
Laporan lengkap (buku digital, format akademik BAB 1–5) tersedia di [`Analisis_Jejaring_Sosial.pdf).

## 7. Catatan Etika
Karena proyek ini menggunakan data sintetis (bukan data pribadi anggota organisasi riil), tidak
ada isu privasi/informed consent. Bila di kemudian hari proyek dikembangkan dengan data
komunikasi organisasi yang sesungguhnya, wajib diterapkan: transparansi tujuan penelitian,
anonimisasi identitas, persetujuan subjek, dan pertimbangan bahwa **data publik tidak otomatis
bebas etika untuk dianalisis**.

## Referensi
- Wasserman, S., & Faust, K. (1994). *Social Network Analysis: Methods and Applications*. Cambridge University Press.
- Newman, M. E. J. (2018). *Networks* (2nd ed.). Oxford University Press.
- Easley, D., & Kleinberg, J. (2010). *Networks, Crowds, and Markets*. Cambridge University Press.
