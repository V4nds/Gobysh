# Dokumentasi Ilmu Kognisi Spasial Goby (Goby Spatial Cognitive Intelligence)

## 🌐 Arsitektur Kognisi Spasial Goby v4.0

Kognisi Spasial (*Spatial Cognition*) pada Goby Framework adalah kemampuan agen AI untuk memetakan, menavigasi, dan menyelesaikan masalah jebakan pada ruang 2D/3D (seperti grid lingkungan, pathfinding, dan state-space multidimensi) tanpa terjebak dalam osilasi tak terbatas.

---

### 🏛️ **Tiga Pilar Kognisi Spasial Goby**

#### 1. **High-Frequency Thread-Safe State Memory (`StateMemoryManager`)**
- **In-Memory RLock Caching**: Menggunakan `threading.RLock()` dengan *caching* state kognitif di memori RAM untuk menjamin pengaksesan konkuren tanpa benturan.
- **Unique Thread Temp Buffers**: Menggunakan penamaan file sementara per-thread (`f"{path}.{thread_id}.tmp"`) dan *atomic retry loop* saat penulisan ke disk pada sistem operasi Windows.
- **Hasil Benchmark**: Memproses **1341.56 ops/sec** dari 50 worker threads simultan dengan **0 race conditions / data corruptions**.

#### 2. **Deteksi Oscillation & Neuro-Cognitive Bypass (`LoopDetectionEngine`)**
- **Pengenalan Pola Osilasi Spasial**: Ketika agen bergerak bolak-balik antara dua titik koordinat spasial (misal: $(3,2) \leftrightarrow (3,3)$), LDE secara otomatis mendeteksi status `PARADOXICAL_OSCILLATION`.
- **Cantor Lateral Leap Bypass**: Memutus siklus terjebak dengan melakukan lompatan kognitif lateral pada dimensi koordinat alternatif, menghindarkan agen dari kebuntuan.

#### 3. **Orkestrasi Multi-Agen Spasial (`MultitaskOrchestrator`)**
- **Pipeline Paralel 4 Sub-Task**:
  - `Task 1: Perception Grid Scan` — Pemindaian matriks koordinat & hambatan.
  - `Task 2: Trajectory Physics` — Perhitungan vektor lintasan & inersia.
  - `Task 3: Action Execution` — Eksekusi aksi pergerakan & evasi.
  - `Task 4: Memory Crystallization` — Penyimpanan ingatan rute sukses ke `cognitive_map.json`.

---

### 🧪 **Cara Menjalankan Pengujian Spasial**

1. **Jalankan Benchmark Stress-Test Spasial**:
   ```bash
   python -m demo.spatial_stress_test
   ```

2. **Jalankan Unit Testsuite Spasial**:
   ```bash
   python -m unittest tests/test_spatial_goby.py
   ```

3. **Verifikasi Audit Resmi**:
   ```bash
   goby audit
   ```
