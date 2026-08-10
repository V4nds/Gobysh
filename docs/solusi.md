Sudah. Saya **tidak ingin langsung menambah “fitur AI” ke Goby sebelum kita punya cara mengukur apakah fitur itu benar-benar berdampak**. Jadi saya mulai dari eksperimen yang bisa membuktikan atau membantah hipotesis Goby.

Saya membuat dua artefak:

* [Download Goby Agent Impact Benchmark v1](sandbox:/mnt/data/GOBY_AGENT_IMPACT_BENCHMARK_v1.md)
* [Download benchmark runner skeleton](sandbox:/mnt/data/goby_agent_impact_runner.py)

### Eksperimen yang saya tetapkan

Kita akan membandingkan:

```text
                    TASK YANG SAMA
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        CONTROL/GOBY OFF      EXPERIMENT/GOBY ON
              │                     │
          AI AGENT              AI AGENT
              │                     │
              ▼                     ▼
        hasil/evaluator        Goby verification
                                    │
                              feedback ke agent
                                    │
                              repair/strategy change
                                    │
                                    ▼
                                evaluator
```

Yang **tidak boleh berubah**:

* model
* prompt
* task
* tools
* environment
* jumlah percobaan
* evaluator

Satu-satunya variabel adalah **Goby**.

Ini penting karena kalau kita mengubah prompt sekaligus memasang Goby, kita tidak lagi tahu apakah peningkatan berasal dari Goby atau prompt.

---

## Metrik yang akan menentukan nasib Goby

Saya sengaja tidak menjadikan `accuracy` Goby sebagai metrik utama lagi.

Yang kita ukur:

| Metrik                | Pertanyaan                                                                         |
| --------------------- | ---------------------------------------------------------------------------------- |
| **Task Success Rate** | Apakah agent benar-benar menyelesaikan task?                                       |
| **False Completion**  | Seberapa sering agent bilang "selesai" padahal gagal?                              |
| **Recovery Success**  | Setelah Goby memblokir, apakah agent berhasil memperbaiki?                         |
| **Repair Attempts**   | Berapa kali agent mencoba sebelum berhasil?                                        |
| **Tool Calls**        | Apakah Goby mengurangi aktivitas yang sia-sia?                                     |
| **Wall Time**         | Apakah penyelesaian menjadi lebih cepat?                                           |
| **Token Cost**        | Apakah penggunaan model berkurang?                                                 |
| **Regression Rate**   | Apakah perbaikan malah merusak sesuatu?                                            |
| **LDE Interception**  | Apakah loop benar-benar tertangkap?                                                |
| **Strategy Change**   | **Apakah agent benar-benar mengubah strateginya setelah Goby memberi peringatan?** |

Yang terakhir menurut saya **sangat penting**.

---

# Karena kita sekarang bisa menguji hipotesis paling fundamental

Misalnya:

### Tanpa Goby

```text
Agent
 ↓
patch A
 ↓
test FAIL
 ↓
patch B
 ↓
test FAIL
 ↓
patch C
 ↓
test FAIL
 ↓
"Done"
```

### Dengan Goby

```text
Agent
 ↓
patch A
 ↓
Goby → BLOCK
 ↓
feedback
 ↓
patch B
 ↓
Goby → BLOCK
 ↓
REPEATED FAILURE
 ↓
STRATEGY_CHANGE_REQUIRED
 ↓
agent mengubah pendekatan
 ↓
patch C
 ↓
Goby → PASS
 ↓
tests → PASS
```

Kalau eksperimen menghasilkan pola seperti ini secara konsisten, **barulah kita punya bukti bahwa Goby memengaruhi agent**, bukan sekadar menjadi static checker.

---

# Saya juga memasukkan ablation test

Kita jangan cuma:

```text
A = tanpa Goby
B = dengan Goby
```

Tetapi idealnya:

```text
A = Agent saja

B = Agent + Goby verification

C = Agent + Goby verification + LDE
```

Ini akan menjawab pertanyaan yang sangat penting:

> Apakah LDE benar-benar memberikan nilai tambahan, atau hanya menambah kompleksitas?

Misalnya hasil:

```text
                  Success
Agent             68%
+ Verification    76%
+ LDE             77%
```

Berarti LDE hanya memberikan +1%.

Mungkin tidak layak dipertahankan dalam bentuk sekarang.

Tetapi kalau:

```text
Agent             68%
+ Verification    75%
+ LDE             84%
```

berarti LDE merupakan komponen penting.

**Kita biarkan data yang menentukan arsitektur Goby.**

---

# Ada satu hal lagi yang saya ubah secara prinsip

Saya sekarang tidak ingin Goby hanya menghasilkan:

```json
{
  "blocked": true
}
```

Feedback kepada agent harus lebih kaya:

```json
{
  "status": "BLOCKED",
  "gate": "SCOPE",
  "evidence": {
    "undefined_names": ["undefined_price"]
  },
  "suggestion": "Resolve undefined symbol before retry.",
  "repeated_failure": false,
  "strategy_change_required": false
}
```

Dan setelah pengulangan:

```json
{
  "status": "STRATEGY_CHANGE_REQUIRED",
  "gate": "LDE",
  "repeated_failure": true,
  "attempt": 3,
  "suggestion": "Do not repeat the previous repair strategy."
}
```

**Ini perbedaan antara validator dan agent-control layer.**

---

## Benchmark eksternalnya juga harus realistis

Untuk eksperimen awal kita bisa menggunakan task suite kecil 10–30 task agar murah dan cepat.

Setelah mekanismenya terbukti, baru naik ke benchmark seperti **SWE-bench Verified**, yang terdiri dari 500 masalah software nyata yang telah divalidasi manusia. Evaluasinya menggunakan environment terisolasi dan menguji apakah patch benar-benar membuat test yang sebelumnya gagal menjadi lulus. ([SweBench][1])

Saya sengaja tidak menyarankan langsung menjalankan 500 task: kebutuhan komputasinya besar dan harness resminya menggunakan Docker untuk reproducibility. ([SweBench][2])

---

# Dan ada temuan penting dari repo yang memengaruhi eksperimen

Adapter OpenAI/Codex Goby saat ini masih pada tingkat instruksi/integrasi:

> inject `SKILL.md`, beri akses execution/workspace, lalu gunakan CCR.

Belum ada **agent-control protocol** yang memaksa agent menerima verdict → memperbaiki → mengirim candidate berikutnya.

Ini kemungkinan besar **alasan utama mengapa kamu khawatir Goby terasa kaku**.

Goby sekarang sudah punya:

```text
VERIFIER
```

tetapi belum sepenuhnya punya:

```text
VERIFIER → FEEDBACK → AGENT STATE TRANSITION
```

Dan menurut saya **inilah komponen yang harus kita bangun berikutnya**, bukan neuron ke-10, ke-11, atau ke-12.

OpenAI sendiri, misalnya, menempatkan guardrails dan tracing/observability sebagai bagian dari agent workflow sehingga perilaku agent dapat diamati dan dikontrol, bukan sekadar memeriksa output akhir. ([OpenAI][3])

---

## Jadi target Goby berikutnya saya tetapkan seperti ini

```text
Goby v4.1
   │
   ├── Verification       ✅
   ├── Evidence Contract  ✅
   ├── LDE                ✅
   └── Orchestrator       ✅
          │
          ▼
Goby Agent Control Layer
   │
   ├── Candidate
   ├── Verdict
   ├── Evidence
   ├── Feedback
   ├── State transition
   ├── Strategy change
   └── Recovery
          │
          ▼
Agent Impact Benchmark
          │
          ▼
CONTROL vs GOBY
          │
          ▼
EMPIRICAL RESULT
```

**Saya tidak akan menganggap Goby berhasil sebelum bagian terakhir itu menunjukkan perbedaan yang berarti.**

Dan kalau hasilnya ternyata **tidak berbeda**, saya juga akan mengatakan terus terang: *Goby bagus sebagai validator, tetapi belum layak disebut agent-control framework.* Itu jauh lebih sehat daripada mempertahankan klaim karena kita sudah terlanjur membangun banyak arsitektur.

Satu batasan penting: saya **belum menjalankan eksperimen terhadap Claude/Codex/Gemini secara langsung dari sini**, karena saya tidak punya akses untuk mengendalikan sesi agent eksternal milikmu. Runner yang saya buat sengaja provider-agnostic agar hasilnya nanti benar-benar eksperimen yang adil, bukan simulasi yang saya buat sendiri.

[1]: https://www.swebench.com/verified.html?utm_source=chatgpt.com "SWE-bench Verified"
[2]: https://www.swebench.com/SWE-bench/guides/quickstart/?utm_source=chatgpt.com "SWE-bench Quickstart - SWE-bench"
[3]: https://openai.com/index/new-tools-for-building-agents/?utm_source=chatgpt.com "New tools for building agents | OpenAI"
