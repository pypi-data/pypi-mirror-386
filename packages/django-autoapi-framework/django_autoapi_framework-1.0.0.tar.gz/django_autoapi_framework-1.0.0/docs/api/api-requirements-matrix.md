# 📋 **API Requirements Matrix**

Matrix lengkap kebutuhan tabel dan dependencies untuk setiap API endpoint dalam Academic Management System.

## 📊 **Overview**

### **API Coverage**
- **Total Endpoints**: 50+
- **Primary Tables**: 25+
- **Reference Tables**: 15+
- **Complex Relationships**: 30+

### **Dependency Categories**
- 🔴 **Critical**: Required untuk endpoint functionality
- 🟡 **Important**: Needed untuk complete data representation
- 🟢 **Optional**: Enhancement atau conditional data

---

## 🏫 **ACADEMIC DOMAIN APIs**

### **1. DOSEN API (`/api/v1/academic/dosen/`)**

#### **GET /dosen/** - List All Dosen
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `dosen` | Primary | 🔴 Critical | Main dosen data |
| `agama` | FK | 🟡 Important | Religion information |
| `status_keaktifan_pegawai` | FK | 🟡 Important | Employment status |
| `ikatan_kerja_dosen` | FK | 🟡 Important | Work contract type |
| `status_dosen` | FK | 🟡 Important | Academic rank |

#### **GET /dosen/{id}/** - Dosen Detail
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `dosen` | Primary | 🔴 Critical | Main dosen data |
| `agama` | FK | 🟡 Important | Religion details |
| `status_keaktifan_pegawai` | FK | 🟡 Important | Employment status |
| `ikatan_kerja_dosen` | FK | 🟡 Important | Contract details |
| `status_dosen` | FK | 🟡 Important | Academic rank |
| `penugasan_dosen` | Reverse FK | 🟢 Optional | Assignment history |

#### **POST /dosen/** - Create Dosen
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `dosen` | Primary | 🔴 Critical | New dosen creation |
| `agama` | FK Validation | 🔴 Critical | Religion reference validation |
| `status_keaktifan_pegawai` | FK Validation | 🔴 Critical | Status validation |
| `ikatan_kerja_dosen` | FK Validation | 🔴 Critical | Contract validation |
| `status_dosen` | FK Validation | 🔴 Critical | Rank validation |

#### **GET /dosen/{id}/penugasan/** - Dosen Assignments
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `penugasan_dosen` | Primary | 🔴 Critical | Assignment data |
| `dosen` | FK | 🔴 Critical | Dosen reference |
| `program_studi` | FK | 🟡 Important | Program assignment |
| `semester` | FK | 🟡 Important | Period information |

---

### **2. MAHASISWA API (`/api/v1/academic/mhs/`)**

#### **GET /mhs/** - List Mahasiswa
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `mahasiswa_biodata` | Primary | 🔴 Critical | Student personal data |
| `riwayat_pendidikan_mahasiswa` | FK | 🔴 Critical | Academic records |
| `program_studi` | FK via riwayat | 🟡 Important | Study program |
| `semester` | FK via riwayat | 🟡 Important | Enrollment period |
| `agama` | FK | 🟡 Important | Religion data |
| `wilayah` | FK (multiple) | 🟢 Optional | Location data |

#### **GET /mhs/{id}/** - Mahasiswa Detail Complete
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `mahasiswa_biodata` | Primary | 🔴 Critical | Complete personal data |
| `riwayat_pendidikan_mahasiswa` | FK | 🔴 Critical | Academic history |
| `program_studi` | FK via riwayat | 🟡 Important | Study program details |
| `semester` | FK via riwayat | 🟡 Important | All semester data |
| `agama` | FK | 🟡 Important | Religion information |
| `wilayah` | FK (birth/address) | 🟡 Important | Geographic data |
| `jenis_keluar` | FK via riwayat | 🟢 Optional | Exit status |
| `pembiayaan` | FK via riwayat | 🟢 Optional | Funding information |

#### **POST /mhs/import/** - Import Mahasiswa Data
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `mahasiswa_biodata` | Primary Create | 🔴 Critical | Biodata creation |
| `riwayat_pendidikan_mahasiswa` | Related Create | 🔴 Critical | Academic record creation |
| `program_studi` | FK Validation | 🔴 Critical | Program validation |
| `semester` | FK Validation | 🔴 Critical | Period validation |
| `agama` | FK Validation | 🔴 Critical | Religion validation |
| `wilayah` | FK Validation | 🟡 Important | Location validation |
| `jenis_keluar` | FK Validation | 🟢 Optional | Exit type validation |
| `pembiayaan` | FK Validation | 🟢 Optional | Funding validation |
| `jalur_masuk` | FK Validation | 🟢 Optional | Entry path validation |

---

### **3. KURIKULUM API (`/api/v1/academic/kurikulum/`)**

#### **GET /kurikulum/** - List Kurikulum
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `kurikulum` | Primary | 🔴 Critical | Curriculum data |
| `program_studi` | FK | 🟡 Important | Program association |
| `semester` | FK | 🟡 Important | Starting semester |

#### **GET /kurikulum/{id}/matakuliah/** - Kurikulum Subjects
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `matkul_kurikulum` | Primary | 🔴 Critical | Subject mappings |
| `kurikulum` | FK | 🔴 Critical | Curriculum reference |
| `mata_kuliah` | FK | 🔴 Critical | Subject details |
| `program_studi` | FK | 🟡 Important | Program context |
| `semester` | FK | 🟡 Important | Period context |
| `jenis_mata_kuliah` | FK via matkul | 🟡 Important | Subject type |
| `kelompok_mata_kuliah` | FK via matkul | 🟡 Important | Subject group |

#### **POST /kurikulum/{id}/matakuliah/** - Add Subject to Curriculum
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `matkul_kurikulum` | Primary Create | 🔴 Critical | New mapping creation |
| `kurikulum` | FK Validation | 🔴 Critical | Curriculum validation |
| `mata_kuliah` | FK Validation | 🔴 Critical | Subject validation |
| `program_studi` | FK Validation | 🔴 Critical | Program validation |
| `semester` | FK Validation | 🔴 Critical | Period validation |

---

### **4. KULIAH API (`/api/v1/academic/kuliah/`)**

#### **GET /kuliah/kelas/** - List Classes
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `kelas_kuliah` | Primary | 🔴 Critical | Class data |
| `mata_kuliah` | FK | 🟡 Important | Subject information |
| `program_studi` | FK | 🟡 Important | Program context |
| `semester` | FK | 🟡 Important | Period context |
| `dosen` | FK | 🟡 Important | Lecturer information |

#### **POST /kuliah/kelas/** - Create Class
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `kelas_kuliah` | Primary Create | 🔴 Critical | New class creation |
| `mata_kuliah` | FK Validation | 🔴 Critical | Subject validation |
| `program_studi` | FK Validation | 🔴 Critical | Program validation |
| `semester` | FK Validation | 🔴 Critical | Period validation |
| `dosen` | FK Validation | 🟢 Optional | Lecturer assignment |

#### **GET /kuliah/kelas/{id}/pengajar/** - Class Lecturers
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `pengajar` | Primary | 🔴 Critical | Teaching assignments |
| `penugasan_dosen` | FK | 🔴 Critical | Lecturer assignment |
| `kelas_kuliah` | FK | 🔴 Critical | Class reference |
| `substansi_kuliah` | FK | 🟡 Important | Subject content |
| `jenis_evaluasi` | FK | 🟡 Important | Evaluation type |

#### **POST /kuliah/kelas/{id}/pengajar/** - Add Lecturer to Class
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `pengajar` | Primary Create | 🔴 Critical | New assignment creation |
| `penugasan_dosen` | FK Validation | 🔴 Critical | Lecturer validation |
| `kelas_kuliah` | FK Validation | 🔴 Critical | Class validation |
| `substansi_kuliah` | FK Validation | 🟢 Optional | Content validation |
| `jenis_evaluasi` | FK Validation | 🟢 Optional | Evaluation validation |

#### **GET /kuliah/kelas/{id}/peserta/** - Class Participants
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `nilai` | Primary | 🔴 Critical | Enrollment records |
| `mahasiswa_biodata` | FK | 🔴 Critical | Student data |
| `riwayat_pendidikan_mahasiswa` | FK | 🔴 Critical | Academic records |
| `kelas_kuliah` | FK | 🔴 Critical | Class reference |
| `mata_kuliah` | FK via kelas | 🟡 Important | Subject context |
| `program_studi` | FK via riwayat | 🟡 Important | Program context |

---

### **5. JADWAL API (`/api/v1/academic/jadwal/`)**

#### **GET /jadwal/** - List Schedules
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `jadwal` | Primary | 🔴 Critical | Schedule data |
| `kelas_kuliah` | FK | 🔴 Critical | Class reference |
| `hari` | FK | 🔴 Critical | Day information |
| `sesi` | FK | 🔴 Critical | Time slot |
| `ruang` | FK | 🔴 Critical | Room information |

#### **POST /jadwal/** - Create Schedule
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `jadwal` | Primary Create | 🔴 Critical | New schedule creation |
| `kelas_kuliah` | FK Validation | 🔴 Critical | Class validation |
| `hari` | FK Validation | 🔴 Critical | Day validation |
| `sesi` | FK Validation | 🔴 Critical | Time validation |
| `ruang` | FK Validation | 🔴 Critical | Room validation |
| `jadwal` (existing) | Conflict Check | 🔴 Critical | Schedule conflict detection |

#### **POST /jadwal/check-bentrok/** - Check Schedule Conflicts
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `jadwal` | Query All | 🔴 Critical | Conflict detection |
| `hari` | FK Reference | 🔴 Critical | Day matching |
| `sesi` | FK Reference | 🔴 Critical | Time overlap check |
| `ruang` | FK Reference | 🔴 Critical | Room availability |

---

### **6. NILAI API (`/api/v1/academic/nilai/`)**

#### **GET /nilai/kelas/{id}/peserta/** - Class Grades
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `nilai` | Primary | 🔴 Critical | Final grades |
| `mahasiswa_biodata` | FK | 🔴 Critical | Student information |
| `riwayat_pendidikan_mahasiswa` | FK | 🔴 Critical | Academic records |
| `kelas_kuliah` | FK | 🔴 Critical | Class context |
| `mata_kuliah` | FK via kelas | 🟡 Important | Subject information |
| `program_studi` | FK via riwayat | 🟡 Important | Program context |
| `komponen_evaluasi_nilai` | Related | 🟡 Important | Grade components |
| `komponen_evaluasi_kelas` | FK via komponen | 🟡 Important | Evaluation settings |

#### **POST /nilai/komponen/** - Input Component Score
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `komponen_evaluasi_nilai` | Primary Create | 🔴 Critical | Component score creation |
| `riwayat_pendidikan_mahasiswa` | FK Validation | 🔴 Critical | Student validation |
| `semester` | FK Validation | 🔴 Critical | Period validation |
| `mata_kuliah` | FK Validation | 🔴 Critical | Subject validation |
| `kelas_kuliah` | FK Validation | 🔴 Critical | Class validation |
| `komponen_evaluasi_kelas` | FK Validation | 🔴 Critical | Component validation |
| `nilai` | Update Target | 🔴 Critical | Final grade recalculation |

#### **PUT /nilai/komponen/{id}/** - Update Component Score
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `komponen_evaluasi_nilai` | Primary Update | 🔴 Critical | Component score update |
| `nilai` | Calculation Target | 🔴 Critical | Final grade recalculation |
| `komponen_evaluasi_kelas` | FK Reference | 🟡 Important | Weight information |

---

### **7. KRS API (`/api/v1/academic/krs/`)**

#### **GET /krs/mahasiswa/{nim}/** - Student Course Registration
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `nilai` | Primary | 🔴 Critical | Registration records |
| `riwayat_pendidikan_mahasiswa` | FK | 🔴 Critical | Student lookup |
| `mahasiswa_biodata` | FK via riwayat | 🔴 Critical | Student data |
| `program_studi` | FK via riwayat | 🟡 Important | Program context |
| `mata_kuliah` | FK via nilai | 🟡 Important | Subject details |
| `kelas_kuliah` | FK via nilai | 🟡 Important | Class information |
| `jadwal` | Related via kelas | 🟡 Important | Schedule information |
| `hari` | FK via jadwal | 🟡 Important | Day information |
| `sesi` | FK via jadwal | 🟡 Important | Time information |
| `ruang` | FK via jadwal | 🟡 Important | Room information |

#### **GET /krs/mahasiswa/{nim}/semester/{semester_id}/** - Semester KRS
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `nilai` | Primary Filtered | 🔴 Critical | Semester-specific records |
| `semester` | Filter Context | 🔴 Critical | Period filter |
| `riwayat_pendidikan_mahasiswa` | FK | 🔴 Critical | Student reference |
| `mahasiswa_biodata` | FK via riwayat | 🔴 Critical | Student data |
| `mata_kuliah` | FK via nilai | 🟡 Important | Subject details |
| `kelas_kuliah` | FK via nilai | 🟡 Important | Class information |
| `jadwal` | Related via kelas | 🟡 Important | Schedule details |

---

## 🔗 **AUTHENTICATION & USER APIs**

### **8. AUTH API (`/api/v1/auth/`)**

#### **POST /auth/login/** - User Login
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `auth_user` | Primary | 🔴 Critical | User authentication |
| `user_profile` | FK | 🟡 Important | Profile information |
| `django_group` | M2M | 🟡 Important | Permission groups |

#### **GET /auth/me/** - Current User Info
| Table | Relationship | Dependency | Purpose |
|-------|-------------|------------|---------|
| `auth_user` | Primary | 🔴 Critical | User data |
| `user_profile` | FK | 🟡 Important | Extended profile |
| `django_group` | M2M | 🟡 Important | User permissions |
| `program_studi` | FK via profile | 🟢 Optional | Access scope |

---

## 📊 **Complex Dependency Analysis**

### **High-Dependency Endpoints**
| Endpoint | Table Count | Complexity | Notes |
|----------|-------------|------------|-------|
| `GET /mhs/{id}/` | 10+ | Very High | Complete student profile |
| `GET /nilai/kelas/{id}/peserta/` | 12+ | Very High | Grade management with components |
| `GET /krs/mahasiswa/{nim}/` | 15+ | Extreme | Full academic schedule |
| `POST /mhs/import/` | 8+ | High | Bulk data import |
| `POST /nilai/komponen/` | 7+ | High | Grade calculation |

### **Performance Critical Endpoints**
| Endpoint | Optimization Strategy | Tables Optimized |
|----------|----------------------|------------------|
| `GET /dosen/` | `select_related` | `agama`, `status_*` |
| `GET /mhs/` | `select_related` + `prefetch_related` | `riwayat_pendidikan`, `program_studi` |
| `GET /jadwal/` | `select_related` | `kelas_kuliah`, `hari`, `sesi`, `ruang` |
| `GET /krs/mahasiswa/{nim}/` | Complex `prefetch_related` | Multiple joined tables |

### **Validation Intensive Endpoints**
| Endpoint | Validation Layers | Critical Validations |
|----------|------------------|---------------------|
| `POST /jadwal/` | 4 layers | Schedule conflict detection |
| `POST /mhs/import/` | 5 layers | Multi-format data validation |
| `POST /nilai/komponen/` | 3 layers | Grade business rules |

---

## 🎯 **Optimization Recommendations**

### **Database Optimizations**
1. **Indexes**: Add composite indexes untuk frequently queried combinations
2. **Foreign Keys**: Ensure all FK relationships have proper indexes
3. **Partitioning**: Consider partitioning large tables by semester

### **Query Optimizations**
1. **Select Related**: Use untuk FK relationships yang selalu dibutuhkan
2. **Prefetch Related**: Use untuk reverse FK dan M2M relationships
3. **Only/Defer**: Use untuk large text fields yang tidak selalu dibutuhkan

### **Caching Strategies**
1. **Reference Tables**: Cache static data (agama, hari, sesi)
2. **User Context**: Cache user profile dan permissions
3. **Computed Data**: Cache expensive calculations (GPA, SKS totals)

---

**🚀 This matrix provides complete dependency mapping untuk optimized API development dan database design dalam Academic Management System.**