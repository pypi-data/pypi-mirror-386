# Repository Guidelines & Team Rules

Dokumen ini menjelaskan aturan kerja bersama di repository ini: cara membuat issue, menulis commit (Conventional Commits), membuat pull request, aturan merge, serta penggunaan Project board (Todo / In Progress / Done). Simpan file ini sebagai **`docs/REPOSITORY_GUIDELINES.md`**.

> **Peran tim**
> - **Lead (Merge Owner):** RedEye1605
> - **Data Science:** Rhendy, Adit, Althaf
> - **Data Analyst:** Vivin, Aufi

---

## Daftar Isi

1. [Branching & Proteksi](#branching--proteksi)
2. [Conventional Commits (Commit Message)](#conventional-commits-commit-message)
3. [Issues: Lifecycle & Penugasan](#issues-lifecycle--penugasan)
4. [Project Board (Todo / In Progress / Done)](#project-board-todo--in-progress--done)
5. [Pull Request (PR) Rules](#pull-request-pr-rules)
6. [Review & Merge Policy](#review--merge-policy)
7. [Testing & Quality](#testing--quality)
8. [Dokumentasi](#dokumentasi)
9. [Rilis & Versioning](#rilis--versioning)
10. [Data & Keamanan](#data--keamanan)
11. [Role & Tanggung Jawab](#role--tanggung-jawab)
12. [Komunikasi & Eskalasi](#komunikasi--eskalasi)
13. [Checklist Sprint (Pembuka & Penutup)](#checklist-sprint-pembuka--penutup)
14. [Template PR & Issue](#template-pr--issue)

---

## Branching & Proteksi

- Branch utama: **`main`** (dilindungi).
- **Dilarang push langsung** ke `main`. Semua perubahan melalui **Pull Request (PR)**.
- Nama branch:
  - `feat/<topik-singkat>` — fitur baru
  - `fix/<issue-id>-<ringkas>` — perbaikan bug
  - `chore/<aktivitas>` — non-feature (CI, tooling, rename)
  - `docs/<topik>` — dokumentasi
- Satu branch = satu tujuan (atomic). Hindari PR gado-gado.

**Rule proteksi (Settings → Branches):**
- Require PR, minimal **1 approval**.
- Require **status checks pass** (CI).
- **Dismiss stale reviews** saat ada commit baru.
- (Opsional) **CODEOWNERS** untuk area tertentu.

---

## Conventional Commits (Commit Message)

Format umum:
```
<type>(<optional-scope>): <short summary>

<body optional>

<footer optional>
```

**Types yang dipakai & kapan digunakan**

- `feat:` — fitur baru untuk user (menambah kemampuan baru).
- `fix:` — memperbaiki bug.
- `docs:` — menambah/memperbarui dokumentasi.
- `style:` — perubahan gaya (formatting, spasi) tanpa mengubah logika.
- `refactor:` — perubahan internal tanpa fitur/bugfix.
- `perf:` — peningkatan performa.
- `test:` — menambah/memperbaiki test.
- `chore:` — pekerjaan rutin (CI, build, deps, rename).
- `build:` — perubahan pada sistem build/dependency.
- `ci:` — perubahan di workflow CI.
- `revert:` — membatalkan commit sebelumnya.
- `BREAKING CHANGE:` — gunakan di footer jika memutus kompatibilitas.

**Contoh baik**
```
feat(core): add basic_clean() with repeated char normalization
fix(patterns): phone regex avoids masking random numbers
docs(readme): add quickstart and api section
chore(ci): cache pip and set concurrency group
refactor(utils): split unicode normalization helpers
```

**Referensi issue/PR**

- Tutup issue otomatis: `Closes #123` (di body/footer).
- Relasi tanpa menutup: `Refs #123` / `Related to #123`.
<img width="1423" height="518" alt="image" src="https://github.com/user-attachments/assets/905818f8-45e1-4b39-a726-253ba289e9c4" />

Ref : https://youtu.be/TKJ4RdhyB5Y?si=nz-loQY3vCL420lj
---

## Issues: Lifecycle & Penugasan

- Semua pekerjaan **wajib** punya **Issue** berisi:
  - **Title (EN)** jelas dan spesifik.
  - **Deskripsi**: *Ringkasan*, *Acceptance Criteria*, *Task checklist*, *Definition of Done*.
  - **Assignee** (pemilik pekerjaan).
  - **Label**: gunakan bawaan GitHub — `enhancement`, `bug`, `documentation`, `question`, `help wanted`, `wontfix`, `duplicate`, `invalid` (sesuai kebutuhan).
- Lead membuat/menggroom **backlog** dan melakukan penugasan:
  - DS tasks → Rhendy / Adit / Althaf.
  - DA tasks → Vivin / Aufi.

**Definition of Ready (DoR)** untuk mulai kerja
- Tujuan jelas, AC jelas, ada test plan singkat, dependensi diketahui.

**Definition of Done (DoD)**
- Kode + test lulus CI.
- Dokumen diperbarui (bila perlu).
- Issue dipindah ke **Done** setelah PR **merged**.
<img width="1893" height="1021" alt="image" src="https://github.com/user-attachments/assets/296d77a2-cd77-4953-8497-6e58bf430545" />

---

## Project Board (Todo / In Progress / Done)

Kolom utama:
- **Todo** — tiket siap dikerjakan (sudah lolos DoR).
- **In Progress** — sedang dikerjakan.
- **Done** — *hanya* setelah PR **merged** & CI hijau.

**Field & aturan pengisian:**
- **Estimate** — Story Points (Fibonacci): `1, 2, 3, 5, 8, 13`  
  Perkiraan: 1≈½ hari, 2≈1 hari, 3≈1.5 hari, 5≈2–3 hari, 8≈4–5 hari, 13=multi-sprint.
- **Size** — T‑shirt size: `XS, S, M, L, XL` (mapping: XS=1, S=2–3, M=5, L=8, XL=13).
- **Iteration** — sprint berjalan (mis. “Iteration 2”).
- **Start/End date** — opsional; isi bila relevan.

**Kebiasaan tim**
- Setiap orang **update status** tiketnya sendiri (drag antar kolom).
- Daily/bi-weekly check: Lead review board, follow-up kendala.
<img width="1645" height="1357" alt="image" src="https://github.com/user-attachments/assets/c297e1eb-c750-4861-975b-a6aea08e2cea" />

---

## Pull Request (PR) Rules

- Buat PR dari branch fitur ke `main`.
- Gunakan **Draft PR** jika belum siap review.
- **Deskripsi PR harus jelas**, gunakan template di akhir file ini.

**Ukuran PR**
- Usahakan PR kecil (ideal < 300 LOC net diff).
- Jika membesar, pertimbangkan pisah menjadi beberapa PR.

**Checklist PR**
- [ ] Lulus CI (lint + test).
- [ ] Sudah menambah/memperbarui unit test.
- [ ] Dokumentasi diperbarui jika perlu.
- [ ] Menyebutkan issue terkait (Closes/Refs).

---

## Review & Merge Policy

- **Hanya Lead** yang boleh melakukan **merge** ke `main`.
- Minimal **1 approval** sebelum merge.
- **Auto-merge** boleh diaktifkan setelah checks hijau.
- Untuk PR sensitif (core logic, API publik), minta review tambahan dari anggota terkait.

**Resolusi konflik**
- Penulis PR bertanggung jawab menyelesaikan konflik merge.

**Rebase vs Merge**
- Prefer **“Squash and merge”** agar sejarah commit rapi. Pastikan judul squash mengikuti **Conventional Commits**.

---

## Testing & Quality

- Unit test wajib untuk fitur/bug yang menyentuh logika.
- Target **coverage ≥ 80%** (jika sudah diaktifkan di CI).
- Nama file test: `tests/test_<modul>.py`.
- Tambahkan edge cases untuk teks Indonesia (emoji, HTML entity, PII, spasi, unicode).

Linting & style:
- Gunakan **ruff** (rule E,F,I), line length 100.
- Hindari dead code dan fungsi terlalu panjang tanpa alasan kuat.

---

## Dokumentasi

- **README**: Quickstart, fitur, contoh singkat, badge CI.
- **`docs/`**: detail API, preset guide, benchmark, edge cases.
- Update dokumen setiap menambah fitur/opsi baru.
- Jika PR mengubah API, sertakan update di README + `docs/api_clean.md`.

---

## Rilis & Versioning

- Gunakan **SemVer**: `MAJOR.MINOR.PATCH`.
- Tag release: `v0.x.y`.
- Release note menyertakan perubahan dari PR berlabel `enhancement`, `fix`, `documentation`.
- Publikasi:
  - **TestPyPI** untuk uji awal.
  - **PyPI** untuk rilis resmi (Trusted Publishing / token).
- Jika ada perubahan putus kompatibilitas, gunakan footer **`BREAKING CHANGE:`** di commit & catat jelas di release notes.

---

## Data & Keamanan

- **Jangan commit secrets** (token/API key) atau data pribadi.
- Folder `data/raw/` dikecualikan dari git (`.gitignore`).
- Aktifkan **Secret scanning** & **Dependabot**.
- PII hanya untuk testing sintetis; masking wajib untuk contoh.

---

## Role & Tanggung Jawab

- **Lead**
  - Grooming backlog, menentukan prioritas & estimasi akhir.
  - Menyetujui dan melakukan merge PR.
  - Menjaga konsistensi API & cadence rilis.
- **DS (Rhendy, Adit dan Althaf)**
  - Implementasi fitur inti (F1–F5), menulis test & benchmark.
  - Menjaga kualitas kode & performa.
- **DA (Vivin dan Aufi)**
  - Menyusun dictionary, pattern PII, edge cases, dan dokumentasi user-facing.
  - Validasi output & contoh.

---

## Komunikasi & Eskalasi

- Gunakan komentar di Issue/PR untuk update teknis.
- Terkendala > 1 hari? Tulis **blokir/kendala** di Issue dan mention Lead.
- Review lama? Ping setelah 24 jam kerja.

---

## Checklist Sprint (Pembuka & Penutup)

**Pembuka Sprint (Lead)**
- [ ] Backlog digroom, Todo jelas (DoR).
- [ ] Estimasi & Size terisi.
- [ ] Iteration/Range tanggal di Project board ditetapkan.
- [ ] Kapasitas per anggota disesuaikan.

**Penutup Sprint**
- [ ] Semua item **Done** sudah merged dan di-archive bila perlu.
- [ ] Release plan / tag disiapkan bila layak rilis.
- [ ] Retrospektif singkat: apa yang baik/kurang, action item.

---

## Template PR & Issue

**Pull Request Template — simpan sebagai `.github/pull_request_template.md`**
```markdown
## Ringkasan
<!-- Tujuan PR -->

## Perubahan Utama
- ...

## Cara Uji / Acceptance Criteria
- ...

## Dampak
- Breaking change? Y/T
- Perf/Deps: ...

## Terkait
Closes #...
```

**Issue Template — Feature request — simpan sebagai `.github/ISSUE_TEMPLATE/feature_request.md`**
```markdown
---
name: Feature request
about: Ajukan fitur/peningkatan
labels: enhancement
---

## Ringkasan
<!-- jelaskan fitur -->

## Acceptance Criteria
- [ ] ...

## Task
- [ ] ...

## Catatan
Terkait: #...
```

**Issue Template — Bug report — simpan sebagai `.github/ISSUE_TEMPLATE/bug_report.md`**
```markdown
---
name: Bug report
about: Laporkan bug
labels: bug
---

## Deskripsi bug
<!-- jelaskan bug -->

## Cara reproduksi
1. ...
2. ...

## Perilaku yang diharapkan
...

## Lingkungan
- OS:
- Python:
- Versi paket:

## Catatan
Terkait: #...
```
