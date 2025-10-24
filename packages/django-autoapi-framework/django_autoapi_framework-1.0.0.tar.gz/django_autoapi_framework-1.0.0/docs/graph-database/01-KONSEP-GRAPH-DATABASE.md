# 📘 Konsep Graph Database untuk Sistem Akademik

## 🎯 Apa itu Graph Database?

Graph Database adalah database yang menggunakan struktur **Graph** (grafik) untuk menyimpan data, terdiri dari:
- **Nodes** (Simpul): Entitas/objek (Mahasiswa, Dosen, Mata Kuliah)
- **Edges** (Sisi/Relationships): Hubungan antar entitas (MENGAMBIL, MENGAJAR, PREREQUISITE)
- **Properties**: Atribut dari nodes dan relationships

### **Perbedaan dengan Relational Database**

| Aspek | Relational DB (PostgreSQL) | Graph DB (Neo4j) |
|-------|---------------------------|------------------|
| **Struktur** | Tabel dengan baris & kolom | Nodes dengan relationships |
| **Relasi** | Foreign Keys + JOINs | Direct relationships (pointers) |
| **Query Relasi** | Multiple JOINs (lambat) | Traversal (sangat cepat) |
| **Use Case** | CRUD operations, transaksi | Relasi kompleks, social network |
| **Performa JOIN** | O(n log n) - melambat saat kompleks | O(1) - konstan |

### **Kapan Menggunakan Graph Database?**

✅ **Gunakan Graph DB untuk:**
- Social network (teman, teman dari teman)
- Recommendation engine (rekomendasi berdasarkan pola)
- Prerequisite chains (mata kuliah prasyarat)
- Path finding (jalur terpendek)
- Network analysis (analisis jaringan)
- Fraud detection
- Knowledge graphs

❌ **JANGAN gunakan Graph DB untuk:**
- Simple CRUD operations
- Reporting/analytics sederhana
- Data yang tidak saling berhubungan
- Transactions yang kompleks

---

## 🏗️ Arsitektur Hybrid (PostgreSQL + Neo4j)

### **Strategi yang Direkomendasikan**

```
┌─────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                     │
│              (Django REST API / GraphQL)                 │
└─────────────────┬───────────────────────┬───────────────┘
                  │                       │
        ┌─────────▼─────────┐   ┌────────▼────────┐
        │   PostgreSQL      │   │     Neo4j       │
        │  (Master Data)    │   │ (Relationships) │
        ├───────────────────┤   ├─────────────────┤
        │ • Mahasiswa       │   │ • MahasiswaNode │
        │ • Dosen           │   │ • DosenNode     │
        │ • MataKuliah      │   │ • Relationships │
        │ • Kelas           │   │ • Graph Queries │
        │ • Nilai           │   │                 │
        │ • CRUD Ops        │   │                 │
        └─────────┬─────────┘   └────────┬────────┘
                  │                      │
                  └──────── Sync ────────┘
                    (Management Command)
```

### **Prinsip Pembagian Tugas**

1. **PostgreSQL** (Source of Truth)
   - Menyimpan semua master data
   - Handle CRUD operations
   - Transaksi ACID
   - Reporting & analytics

2. **Neo4j** (Relationship Engine)
   - Menyimpan copy data dalam bentuk graph
   - Handle relationship queries
   - Social network features
   - Recommendation engine

3. **Sync Mechanism**
   - PostgreSQL → Neo4j (one-way sync)
   - Bisa full sync atau incremental
   - Triggered via management command atau Django signals

---

## 📊 Contoh Kasus: Sistem Akademik

### **Entitas (Nodes)**

```
MahasiswaNode
├── nim (unique)
├── nama
├── email
├── angkatan
├── ipk
└── status

DosenNode
├── nip (unique)
├── nama
├── nidn
├── email
└── jabatan

MataKuliahNode
├── kode (unique)
├── nama
├── sks
└── semester

KelasNode
├── id_kelas (unique)
├── nama_kelas
├── semester
└── kapasitas

ProdiNode
├── kode_prodi (unique)
├── nama_prodi
└── jenjang
```

### **Relationships (Edges)**

```
(Mahasiswa)-[MENGAMBIL]->(Kelas)
(Mahasiswa)-[LULUS]->(MataKuliah)
(Mahasiswa)-[DIBIMBING_OLEH]->(Dosen)
(Mahasiswa)-[KULIAH_DI]->(Prodi)
(Mahasiswa)-[TEMAN_SEKELAS]->(Mahasiswa)

(Dosen)-[MENGAJAR]->(Kelas)
(Dosen)-[MENGAJAR]->(MataKuliah)
(Dosen)-[BERTUGAS_DI]->(Prodi)

(MataKuliah)-[PREREQUISITE]->(MataKuliah)
(MataKuliah)-[BAGIAN_DARI]->(Prodi)

(Kelas)-[UNTUK_MATKUL]->(MataKuliah)
(Kelas)-[DI_PRODI]->(Prodi)
```

### **Visualisasi Graph**

```
      (Mahasiswa)
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
(Kelas)(Prodi)(Dosen)
    │           │
    ▼           ▼
(MataKuliah)─►(MataKuliah)
               [PREREQUISITE]
```

---

## 🔍 Query Examples

### **1. Find Classmates (Teman Sekelas)**

**Cypher (Neo4j):**
```cypher
MATCH (m1:MahasiswaNode {nim: '11201800001'})
      -[:MENGAMBIL]->(k:KelasNode)
      <-[:MENGAMBIL]-(m2:MahasiswaNode)
WHERE m1 <> m2
RETURN m2.nama, COUNT(k) as kelas_bersama
ORDER BY kelas_bersama DESC
```

**SQL (PostgreSQL) - untuk perbandingan:**
```sql
SELECT m2.nama, COUNT(DISTINCT k.id) as kelas_bersama
FROM mahasiswa m1
JOIN krs krs1 ON m1.nim = krs1.nim
JOIN kelas k ON krs1.id_kelas = k.id
JOIN krs krs2 ON k.id = krs2.id_kelas
JOIN mahasiswa m2 ON krs2.nim = m2.nim
WHERE m1.nim = '11201800001' AND m2.nim != '11201800001'
GROUP BY m2.nim, m2.nama
ORDER BY kelas_bersama DESC
```

**Performa:**
- SQL: 5-10 detik (4 JOINs)
- Cypher: 50-100ms (**100x lebih cepat**)

### **2. Friends of Friends (2-Hop)**

**Cypher:**
```cypher
MATCH (m:MahasiswaNode {nim: '11201800001'})
      -[:MENGAMBIL]->(:KelasNode)
      <-[:MENGAMBIL]-(teman)
      -[:MENGAMBIL]->(:KelasNode)
      <-[:MENGAMBIL]-(fof:MahasiswaNode)
WHERE fof <> m AND NOT (m)-[:MENGAMBIL]->()<-[:MENGAMBIL]-(fof)
RETURN fof.nama, COUNT(DISTINCT teman) as mutual_friends
ORDER BY mutual_friends DESC
```

**SQL:**
```sql
-- Sangat kompleks dan lambat (6-8 JOINs, multiple subqueries)
```

**Performa:**
- SQL: 30-60 detik atau timeout
- Cypher: 200ms (**150-300x lebih cepat**)

### **3. Prerequisite Chain**

**Cypher:**
```cypher
MATCH path = (mk:MataKuliahNode {kode: 'IF401'})
             -[:PREREQUISITE*]->(prereq)
RETURN path
```

**Kelebihan:**
- Recursive query sangat mudah
- Visualisasi path otomatis
- Performa konstan tidak peduli kedalaman

---

## 💡 Use Cases untuk Sistem Akademik

### **1. Social Network Features**
- Cari teman sekelas
- Rekomendasi teman berdasarkan kelas yang sama
- Analisis "siapa yang paling banyak teman"
- Network visualization

### **2. Recommendation Engine**
- Rekomendasi mata kuliah berdasarkan apa yang teman ambil
- Rekomendasi dosen pembimbing
- Rekomendasi topik skripsi

### **3. Academic Path Analysis**
- Prerequisite chain lengkap
- Shortest path to graduation
- Missing prerequisites
- Suggested course sequence

### **4. Performance Analytics**
- Compare IPK dengan teman sekelas
- Identifikasi high performers
- Study group recommendations

### **5. Research Collaboration**
- Dosen collaboration network
- Co-teaching analysis
- Research group formation

### **6. Anomaly Detection**
- Pola KRS yang tidak wajar
- Fraud detection dalam pendaftaran
- Academic misconduct patterns

---

## 🚀 Keuntungan Graph Database

### **1. Performa Query Relasi**
- Constant time O(1) untuk traversal
- Tidak ada JOIN overhead
- Skalabel untuk relasi kompleks

### **2. Model Data Natural**
- Mirip dengan cara manusia berpikir
- Visualisasi mudah
- Eksplorasi data intuitif

### **3. Flexibility**
- Schema fleksibel
- Mudah tambah relationship baru
- Evolusi model tanpa migration kompleks

### **4. Query Language (Cypher)**
- Mudah dipahami
- Pattern matching powerful
- Native graph operations

---

## ⚠️ Considerations

### **Kekurangan Graph Database**

1. **Kompleksitas Infrastruktur**
   - Perlu maintain 2 database
   - Sync mechanism harus reliable
   - Storage overhead

2. **Learning Curve**
   - Cypher query language baru
   - Graph thinking paradigm
   - Debugging lebih sulit

3. **Konsistensi Data**
   - Eventual consistency
   - Perlu mekanisme sync yang baik
   - Data bisa out-of-sync

4. **Cost**
   - Memory intensive
   - Licensing (untuk enterprise)
   - Operational overhead

### **Mitigasi**

1. **Graceful Degradation**
   - Sistem tetap jalan tanpa graph DB
   - Graph features optional
   - Fallback to SQL queries

2. **Good Sync Strategy**
   - Scheduled batch sync
   - Incremental updates via signals
   - Consistency checks

3. **Clear Separation**
   - PostgreSQL = source of truth
   - Neo4j = query accelerator
   - Always rebuildable from PostgreSQL

---

## 📈 Performance Benchmarks

### **Query Comparison**

| Query Type | PostgreSQL | Neo4j | Speedup |
|------------|-----------|-------|---------|
| Find classmates | 5-10s | 50-100ms | **100x** |
| Friends of friends | 30-60s | 200ms | **150-300x** |
| Prerequisite chain (6 levels) | 2-3s | 20ms | **150x** |
| Course recommendations | 10-15s | 100ms | **150x** |
| Social network stats | 20s | 150ms | **130x** |
| Shortest path | 15-20s | 50ms | **300-400x** |

### **Data Size Impact**

**PostgreSQL:**
- Performa menurun eksponensial dengan kompleksitas relasi
- JOIN cost meningkat dengan jumlah tabel
- Index membantu tapi tidak menyelesaikan masalah fundamental

**Neo4j:**
- Performa relatif konstan
- Traversal O(1) tidak peduli ukuran database
- Memory-intensive tapi worth it untuk relationship queries

---

## 🎓 Kesimpulan

### **Kapan Implement Graph Database?**

✅ **Ya, jika:**
- Sistem punya banyak relasi kompleks
- Social features penting
- Recommendation engine diperlukan
- Path finding/network analysis dibutuhkan
- Query performa critical

❌ **Tidak, jika:**
- Simple CRUD saja
- Budget/resources terbatas
- Tim tidak ada yang familiar dengan graph DB
- Maintenance overhead terlalu tinggi

### **Recommended Approach**

1. **Start Small**: Implementasi untuk 1-2 use case
2. **Measure Impact**: Benchmark performa improvement
3. **Gradual Expansion**: Tambah features bertahap
4. **Always Fallback**: Sistem harus tetap jalan tanpa graph DB

---

**Next:** [02-LANGKAH-IMPLEMENTASI.md](./02-LANGKAH-IMPLEMENTASI.md)
