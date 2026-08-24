# AI-Assisted Spreadsheet Intelligence Workspace

Name: Sheetsly

Core Tagline:
Turn your data into insight.

Supporting Tagline:
Ask anything about your data.

Product Description:
An interactive spreadsheet intelligence workspace that helps users
read, explore, calculate, visualize, and understand spreadsheet data
without requiring advanced Excel or data analytics knowledge.

## 1. Konsep Produk

Platform web berbentuk interactive spreadsheet intelligence workspace
untuk membantu pengguna membaca, memahami, menganalisis,
memvisualisasikan, dan mendapatkan insight dari data spreadsheet
tanpa harus memahami Excel atau data analytics secara mendalam.

Sheetsly memiliki tiga cara utama untuk berinteraksi dengan data:

1. Direct Data Exploration
   User dapat melihat data spreadsheet aktual melalui UI.

2. Click-Based Analysis
   User dapat melakukan operasi analisis melalui UI
   tanpa harus mengetahui formula Excel.

3. Natural Language Analysis
   User dapat bertanya menggunakan bahasa natural
   melalui AI Assistant.

Ketiga mode tersebut menggunakan analytical engine yang sama.

Workspace:
User melihat dan mengontrol data.

Python Data Engine:
User mendapatkan hasil kalkulasi yang deterministik.

AI:
User dapat berinteraksi dengan analytical engine
menggunakan bahasa natural dan mendapatkan penjelasan.

Prinsip utama:

- User cukup upload file Excel.
- Sistem membaca struktur dan data spreadsheet secara programatik.
- Setiap sheet dapat dilihat sebagai tabel aktual melalui UI.
- Python menjadi sumber kebenaran untuk pembacaan, transformasi,
  kalkulasi, dan analisis data.
- AI tidak melakukan kalkulasi secara langsung.
- AI berfungsi sebagai natural-language interface,
  reasoning layer, dan explanation layer.
- AI tidak boleh mengarang fakta yang tidak terdapat pada data.
- Jika konteks bisnis belum cukup, AI wajib meminta klarifikasi.
- Semua insight harus dapat ditelusuri kembali ke data sumber.
- Sheetsly bukan hanya chatbot; workspace interaktif merupakan
  primary interface untuk eksplorasi dan analisis data.
- AI bukan satu-satunya cara melakukan analisis.
- Setiap operasi yang dapat dilakukan melalui AI idealnya juga
  dapat dilakukan melalui UI secara deterministik.
- Click-based analysis dan AI analysis harus menggunakan
  analytical engine yang sama.
- User tidak perlu mengetahui formula Excel untuk melakukan
  operasi analisis dasar.
- AI dapat menerjemahkan bahasa natural menjadi analytical instruction,
  sedangkan Python Data Engine mengeksekusi instruction tersebut.
- UI dapat menampilkan analytical instruction yang sedang digunakan
  agar user memahami bagaimana hasil diperoleh.
- Setiap hasil analisis harus dapat menunjukkan dataset, sheet,
  table, column, filter, operation, dan source range yang digunakan.

# 2. Tujuan Utama

Menyederhanakan pekerjaan spreadsheet dan data analysis bagi pengguna
yang:

- Tidak menguasai Excel.
- Tidak memahami formula Excel.
- Tidak terbiasa membuat PivotTable.
- Tidak memahami data analytics.
- Kesulitan membuat chart.
- Memiliki data bisnis tetapi tidak tahu cara menganalisisnya.
- Bisa menggunakan Excel tetapi ingin melakukan analisis lebih cepat.
- Membutuhkan cara sederhana untuk memahami data operasional.
- Membutuhkan bantuan untuk menemukan pola, anomali, atau perbandingan
  dari data.

Sheetsly tidak hanya ditujukan untuk pengguna yang tidak bisa Excel.

Sheetsly juga ditujukan untuk pengguna yang memahami spreadsheet
tetapi ingin mempercepat pekerjaan analisis dan reporting.

User cukup melakukan:

Upload Spreadsheet
↓
Workbook Inspection
↓
Sheet & Table Detection
↓
Data Profiling
↓
Data Quality Assessment
↓
Workspace Ready
↓
User melihat actual spreadsheet data
↓
User memilih mode interaksi:

    ┌──────────────────────┬──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼

Explore Click Analyze Ask AI
│ │ │
│ │ │
└──────────────┬───────┴──────────────┬───────┘
▼ ▼
Analytical Instruction
│
▼
Python Data Engine
│
▼
Verified Result
│
┌────────┼─────────┐
▼ ▼ ▼
Table Chart Insight
│ │ │
└────────┼─────────┘
▼
Source Trace
│
▼
Workspace UI

# 3. Prinsip Arsitektur

## Source of Truth

Data asli spreadsheet adalah sumber kebenaran utama.

AI tidak boleh menjadi sumber angka.

AI tidak boleh:

- Mengarang angka.
- Mengestimasi angka tanpa diberi label sebagai estimasi.
- Mengisi data yang tidak tersedia.
- Menganggap struktur tabel tanpa validasi.
- Menganggap identitas perusahaan tanpa informasi pendukung.
- Membuat kesimpulan bisnis tanpa dasar data.

Python Data Engine menjadi sumber kebenaran untuk:

- Reading
- Parsing
- Validation
- Transformation
- Calculation
- Aggregation
- Statistical analysis
- Visualization data

# 4. Technology Stack

## Frontend

Next.js

Digunakan sebagai frontend JavaScript untuk membangun
interactive spreadsheet intelligence workspace.

Komponen utama:

- Landing page
- File upload interface
- Workbook overview
- Sheet navigation
- Actual spreadsheet viewer
- Table selector
- Data explorer
- Analysis operation panel
- Filter builder
- Grouping interface
- Calculation interface
- Cross-sheet relationship interface
- Chart viewer
- Result viewer
- Source trace viewer
- Calculation trace viewer
- AI chat interface
- AI-generated suggested questions
- AI-generated suggested analysis
- Dashboard
- Insight panel
- Data quality warning panel
- Business context interface

## Backend

FastAPI

Digunakan sebagai backend Python dan orchestration layer untuk:

- API layer
- File ingestion
- Workbook inspection
- Spreadsheet parsing
- Sheet analysis
- Table detection
- Orientation detection
- Data profiling
- Data quality analysis
- Schema detection
- Relationship detection
- Data transformation
- Analytical instruction processing
- Deterministic calculation
- Filtering
- Grouping
- Sorting
- Aggregation
- Pivot operation
- Join / merge
- Statistical analysis
- Visualization generation
- Source traceability
- Calculation lineage
- AI orchestration
- AI guardrail
- Business context management
- Session context management

## Spreadsheet Processing

Python ecosystem:

- Pandas
- OpenPyXL
- Optional Polars untuk dataset besar
- Library spreadsheet lain sesuai kebutuhan format

## Visualization

Matplotlib / Seaborn

Digunakan oleh backend untuk menghasilkan visualisasi
berdasarkan hasil analisis yang telah dihitung oleh Python.

## AI Layer

LLM digunakan untuk:

- Memahami pertanyaan user.
- Mengidentifikasi intent.
- Menentukan data yang dibutuhkan.
- Menentukan operasi analisis.
- Meminta klarifikasi.
- Menjelaskan hasil.
- Memberikan insight berbasis data.
- Memberikan rekomendasi berbasis evidence.

# AI as Interface Layer

AI bukan analytical engine.

AI berfungsi sebagai natural-language interface
untuk mengontrol dan berinteraksi dengan analytical engine.

AI dapat:

- Memahami pertanyaan user.
- Mengidentifikasi intent.
- Mengidentifikasi dataset yang relevan.
- Mengidentifikasi sheet yang relevan.
- Mengidentifikasi table yang relevan.
- Mengidentifikasi column yang relevan.
- Menentukan operation yang dibutuhkan.
- Membuat analytical instruction.
- Meminta klarifikasi jika parameter tidak cukup.
- Mengubah permintaan lanjutan menjadi perubahan analytical instruction.
- Menjelaskan verified result.
- Menghasilkan insight berbasis evidence.
- Menghasilkan recommendation jika business context mencukupi.

AI tidak boleh:

- Mengambil angka dari memorinya sendiri.
- Menghitung angka yang dapat dihitung oleh Python.
- Mengarang isi cell.
- Mengarang struktur spreadsheet.
- Menebak relationship antar tabel tanpa validasi.
- Mengubah analytical instruction tanpa alasan yang dapat ditelusuri.
- Menghasilkan recommendation yang tidak memiliki evidence.

AI berperan sebagai:

Understand
↓
Plan
↓
Request
↓
Interpret
↓
Explain

Python berperan sebagai:

Read
↓
Validate
↓
Transform
↓
Calculate
↓
Aggregate
↓
Validate Result
↓
Trace

# 5. High-Level Architecture

User
│
▼
Next.js Frontend
│
├── File Upload
├── Spreadsheet Viewer
├── Sheet Selector
├── Table Selector
├── Data Explorer
├── Chart Viewer
└── AI Assistant
│
▼
FastAPI Backend
│
├── File Ingestion Layer
├── Spreadsheet Parser
├── Data Profiling Engine
├── Schema Detection Engine
├── Data Validation Engine
├── Data Transformation Engine
├── Analytical Engine
├── Visualization Engine
├── AI Orchestrator
└── Context / Metadata Manager
│
├── Python Data Engine
│
└── LLM
│
▼
Analysis Result
│
├── Table
├── Chart
├── Calculation
├── Explanation
└── Business Insight
│
▼
Next.js Frontend

# Interaction Architecture

Sheetsly memiliki dua primary interaction modes:

## Mode A — Direct Manipulation

User menggunakan UI untuk memilih:

Sheet
↓
Table
↓
Column
↓
Operation
↓
Filter
↓
Grouping
↓
Visualization

Frontend mengirim analytical instruction
ke FastAPI.

FastAPI meneruskan instruction
ke Python Analytical Engine.

Python menghasilkan verified result.

Frontend menampilkan result.

## Mode B — Natural Language

User mengirim pertanyaan ke AI Assistant.

AI mengubah pertanyaan menjadi analytical instruction.

Instruction divalidasi oleh backend.

Python Analytical Engine mengeksekusi instruction.

Hasil dikembalikan bersama source metadata.

AI menjelaskan hasil.

Frontend menampilkan hasil.

## Mode C — Hybrid Interaction

User terlebih dahulu melakukan analisis melalui UI.

Kemudian user melanjutkan dengan AI.

Contoh:

User:
Sheet = Penjualan

Metric = Revenue

Group By = Produk

↓

AI:
"Urutkan berdasarkan revenue terbesar dan
tampilkan hanya 5 produk teratas."

↓

AI menghasilkan perubahan instruction:

Sort:
Revenue DESC

Limit:
5

↓

Python mengeksekusi.

↓

Workspace memperbarui table dan chart.

Sebaliknya, user juga dapat memulai dari AI
dan kemudian melanjutkan analisis melalui UI.

# 6. File Ingestion Pipeline

Ketika user meng-upload Excel:

Upload File
↓
File Validation
↓
Workbook Inspection
↓
Sheet Detection
↓
Sheet Metadata Extraction
↓
Data Profiling
↓
Structure Detection
↓
Schema Detection
↓
Data Quality Assessment
↓
Ready for Analysis

# 7. Workbook Inspection

Sistem harus membaca workbook secara keseluruhan terlebih dahulu.

Informasi yang diperiksa:

- Nama file
- Jumlah sheet
- Nama setiap sheet
- Jumlah baris
- Jumlah kolom
- Used range
- Hidden sheet
- Merged cells
- Empty rows
- Empty columns
- Formula cells
- Text cells
- Numeric cells
- Date cells
- Percentage cells
- Currency-like values
- Duplicate rows
- Null values

# 8. Sheet-Level Data Profiling

Setiap sheet dianalisis secara independen.

Contoh metadata:

Sheet
↓
Dimensions
↓
Potential Header
↓
Potential Data Region
↓
Column Candidates
↓
Data Types
↓
Missing Values
↓
Unique Values
↓
Potential Table

Sistem tidak boleh langsung menganggap seluruh sheet sebagai
satu tabel.

# 9. Data Region Detection

Ini merupakan komponen penting.

Sistem harus menentukan:

- Bagian mana yang merupakan header.
- Bagian mana yang merupakan data.
- Bagian mana yang merupakan judul.
- Bagian mana yang merupakan catatan.
- Bagian mana yang merupakan subtotal.
- Bagian mana yang merupakan footer.
- Apakah terdapat lebih dari satu tabel dalam satu sheet.

Contoh struktur yang harus dapat ditangani:

Judul laporan
Tanggal laporan
Informasi perusahaan

TABEL UTAMA
Header
Data
Data
Data

Catatan
Footer

# 10. Horizontal vs Vertical Data Detection

Sistem tidak boleh memiliki asumsi:

"Semua data pasti tersusun ke bawah."

Sistem harus melakukan structural analysis.

Kemungkinan struktur:

## Vertical Table

Rows = records
Columns = attributes

## Horizontal Table

Columns = records
Rows = attributes

## Multi-Level Header

Header terdiri dari beberapa baris.

## Multiple Tables

Satu sheet memiliki beberapa tabel terpisah.

## Irregular Spreadsheet

Spreadsheet memiliki kombinasi:

- merged cells
- blank rows
- subtotal
- notes
- formulas
- formatting
- multiple sections

# 11. Orientation Detection

Sistem melakukan penilaian terhadap orientasi data.

Candidate:

- Vertical
- Horizontal
- Ambiguous
- Irregular

Jika confidence rendah:

JANGAN MELANJUTKAN ANALISIS OTOMATIS.

Sistem meminta user melakukan konfirmasi.

Contoh UI:

"Struktur data pada Sheet Penjualan terlihat ambigu.
Bagaimana data ini seharusnya dibaca?"

[ Data ke bawah ]
[ Data ke samping ]
[ Pilih area tabel secara manual ]

# 12. Table Detection

Satu sheet dapat memiliki:

- 0 tabel
- 1 tabel
- beberapa tabel

Setiap tabel memiliki metadata:

- Sheet
- Range
- Header
- Orientation
- Number of rows
- Number of columns
- Column names
- Data types
- Confidence score

User dapat memilih tabel tertentu melalui UI.

# 13. Actual Spreadsheet Viewer

User dapat melihat data asli setiap sheet.

UI tidak harus menampilkan Excel mentah.

Frontend menyediakan:

- Sheet sidebar
- Table selector
- Search
- Filter
- Sorting
- Pagination / virtualization
- Column resize
- Column type indicator
- Row number
- Column identifier
- Data preview
- Formula indicator
- Selected cell information

Tujuan:

User tetap dapat melihat data aktual,
tetapi melalui UI yang lebih mudah dipahami.

## Interactive Cell Selection

User dapat memilih:

- Cell
- Row
- Column
- Range

Sistem mengetahui lokasi aktual:

File
↓
Sheet
↓
Cell / Range
↓
Row
↓
Column

Selected cell dapat digunakan untuk:

- Melihat original value.
- Melihat parsed value.
- Melihat data type.
- Melihat formula.
- Melihat source location.
- Memulai analysis terhadap column atau range tersebut.

Namun user tidak mengubah source spreadsheet
secara langsung melalui analysis interface
kecuali fitur editing memang diimplementasikan
secara terpisah.

# Spreadsheet Workspace Layout

Workspace tidak menampilkan spreadsheet sebagai satu-satunya interface.

Workspace terdiri dari beberapa area:

## Sheet Navigator

Menampilkan seluruh sheet dalam workbook.

User dapat berpindah antar sheet.

## Actual Data Viewer

Menampilkan data aktual dari sheet yang dipilih.

Harus mempertahankan:

- Row number
- Column identifier
- Original value
- Cell position
- Formula indicator
- Data type
- Source location

## Analysis Panel

Panel untuk melakukan operasi analisis
tanpa membutuhkan formula Excel.

Kategori operasi:

- Calculate
- Filter
- Sort
- Group
- Compare
- Lookup
- Join
- Pivot
- Transform
- Visualize

## Result Panel

Menampilkan:

- Result table
- KPI
- Calculation result
- Chart
- Explanation
- Insight
- Warning

## AI Assistant

Menjadi natural-language interface
untuk menjalankan analisis dan menjelaskan hasil.

## Source / Trace Panel

Menampilkan asal data dan proses kalkulasi.

# 14. Cell-Level Traceability

Setiap data yang digunakan untuk analisis harus dapat ditelusuri
ke lokasi asalnya.

Minimal metadata:

- File
- Sheet
- Cell / Range
- Row
- Column
- Column name
- Original value
- Parsed value

Contoh konsep:

Analysis Result
↓
Source Data
↓
Sheet
↓
Range
↓
Cell

# 15. Data Type Detection

Setiap kolom dianalisis.

Potential types:

- String
- Integer
- Float
- Currency
- Percentage
- Date
- Datetime
- Boolean
- Category
- Identifier
- Formula
- Unknown

Sistem juga dapat mendeteksi kemungkinan semantic type.

Contoh:

"Product"
→ categorical

"Quantity"
→ numeric measure

"Date"
→ temporal

"Revenue"
→ currency / numeric measure

# 16. Data Quality Engine

Sebelum analisis dilakukan,
sistem harus memeriksa kualitas data.

Checks:

- Missing values
- Duplicate rows
- Duplicate identifiers
- Invalid dates
- Mixed data types
- Text dalam numeric column
- Outliers
- Inconsistent naming
- Inconsistent units
- Empty columns
- Empty rows
- Broken formulas
- Suspicious values

Hasil:

Data Quality Score

dan daftar warning.

Contoh:

"Kolom Quantity memiliki 12 nilai yang tidak dapat dibaca sebagai angka."

# 17. Analytical Engine

Python menjadi deterministic analytical engine
dan satu-satunya sumber kebenaran untuk hasil numerik.

Semua analytical operation dari:

- UI
- AI
- Dashboard
- Visualization
- Export

harus menggunakan Analytical Engine yang sama.

# Analysis Operation Model

Sheetsly tidak berorientasi pada formula Excel.

Sheetsly menggunakan concept of operations.

Contoh:

User memilih:

Operation:
Total

Column:
Revenue

Filter:
Region = Serang

↓

Analytical Instruction:

Operation:
SUM

Column:
Revenue

Filter:
Region = Serang

↓

Python:

SUM(Revenue WHERE Region = Serang)

↓

Result:

Total Revenue:
Rp X

↓

Trace:

Sheet:
Penjualan

Table:
Sales Data

Column:
Revenue

Rows Used:
X rows

Filter:
Region = Serang

# Operation Catalog

Sheetsly menyediakan operation catalog
yang dapat digunakan melalui UI maupun AI.

## Calculate

- Total
- Average
- Minimum
- Maximum
- Median
- Count
- Unique Count

## Conditional Calculate

- Sum by condition
- Sum by multiple conditions
- Count by condition
- Count by multiple conditions
- Conditional classification

## Filter

- Equals
- Not equals
- Contains
- Starts with
- Greater than
- Less than
- Greater than or equal
- Less than or equal
- Between
- Is empty
- Is not empty

## Group

- Group by category
- Group by date
- Group by region
- Group by product
- Group by customer

## Compare

- Compare two periods
- Compare categories
- Compare regions
- Compare products
- Compare current vs previous period

## Lookup / Join

- Lookup by identifier
- Join tables
- Merge sheets
- Match records
- Detect unmatched records

## Transform

- Rename column
- Change data type
- Clean text
- Split column
- Combine column
- Remove duplicates
- Handle missing values

## Visualization

- Bar
- Line
- Pie
- Area
- Scatter
- Histogram
- Box plot
- Heatmap
- Stacked bar
- Time series

User tidak perlu mengetahui nama
formula Excel untuk menggunakan operation tersebut.

## Basic Operations

- SUM
- COUNT
- AVERAGE
- MIN
- MAX
- MEDIAN
- DISTINCT COUNT
- GROUP BY
- FILTER
- SORT
- JOIN
- PIVOT
- RATIO
- PERCENTAGE
- GROWTH
- COMPARISON

## Conditional Operations

Konsep formula Excel diterjemahkan menjadi
analytical operation yang lebih mudah dipahami user.

### SUMIF

Menjumlahkan nilai berdasarkan satu kondisi.

### SUMIFS

Menjumlahkan nilai berdasarkan beberapa kondisi.

### COUNTIF

Menghitung jumlah data berdasarkan satu kondisi.

### COUNTIFS

Menghitung jumlah data berdasarkan beberapa kondisi.

### IF

Membuat conditional classification atau derived value.

### AND / OR

Menggabungkan beberapa kondisi.

### XLOOKUP / VLOOKUP

Digunakan sebagai konsep lookup antar tabel.

Di dalam Sheetsly, user tidak diwajibkan menulis formula.

User cukup menentukan:

Source Table
↓
Match Column
↓
Target Table
↓
Target Match Column
↓
Column to Retrieve

Python melakukan lookup / join.

## Data Operations

- FILTER
- SORT
- GROUP BY
- JOIN
- MERGE
- PIVOT
- UNPIVOT
- DISTINCT
- DUPLICATE DETECTION

## Analytical Operations

- TREND
- GROWTH
- COMPARISON
- RATIO
- PERCENTAGE
- DISTRIBUTION
- CORRELATION
- OUTLIER DETECTION
- SEGMENTATION
- FORECASTING

Operasi lanjutan hanya dijalankan jika
data yang dibutuhkan tersedia dan valid.

# 18. AI Query Pipeline

# AI Query Pipeline

User:
"Produk apa yang paling laku bulan ini?"

↓

AI memahami intent.

↓

AI mengidentifikasi:

Dataset
Sheet
Table
Relevant Columns
Time Filter
Metric
Grouping
Sort
Limit

↓

AI membuat analytical instruction.

↓

FastAPI memvalidasi instruction.

↓

Python Analytical Engine:

Read
↓
Filter
↓
Group
↓
Aggregate
↓
Sort
↓
Validate
↓
Trace

↓

Python menghasilkan:

Result

- Source Metadata
- Calculation Metadata
- Data Quality Status

↓

AI menerima verified result.

↓

AI menjelaskan hasil tanpa mengubah angka.

↓

Frontend menampilkan:

- Answer
- Result Table
- Chart
- Calculation
- Source
- Explanation
- Evidence
- Data Quality Warning

# 19. AI Must Not Calculate

# AI Must Not Calculate

AI tidak menjadi calculator.

AI tidak menjadi source of truth.

AI tidak melakukan operasi numerik final
jika operasi tersebut dapat dilakukan oleh Python.

AI:

Understand
↓
Plan
↓
Create Analytical Instruction
↓
Request Execution
↓
Interpret Verified Result
↓
Explain
↓
Recommend when evidence is sufficient

Python:

Read
↓
Validate
↓
Filter
↓
Transform
↓
Calculate
↓
Aggregate
↓
Validate Result
↓
Generate Trace
↓
Return Verified Result

# 20. AI Guardrail

AI harus memiliki aturan:

1. Jangan mengarang data.
2. Jangan mengarang konteks perusahaan.
3. Jangan mengarang angka.
4. Jangan menganggap kolom memiliki arti tertentu tanpa evidence.
5. Jangan melakukan kalkulasi manual jika Python dapat melakukannya.
6. Jangan memberikan business advice jika konteks minimum belum tersedia.
7. Jika data ambigu, minta klarifikasi.
8. Jika data tidak tersedia, katakan bahwa data tidak tersedia.
9. Jika kesimpulan hanya berupa kemungkinan, tandai sebagai kemungkinan.
10. Semua insight harus memiliki evidence dari dataset.

# 21. Business Context Layer

Spreadsheet tidak selalu menjelaskan konteks bisnis.

Karena itu sistem memiliki Business Context.

Informasi yang dapat diketahui:

- Nama perusahaan
- Industri
- Jenis bisnis
- Produk / jasa
- Target market
- Wilayah operasi
- Periode laporan
- Definisi KPI
- Currency
- Unit
- Tujuan analisis

Context dapat berasal dari:

1. User
2. File metadata
3. Data yang sangat jelas
4. Percakapan sebelumnya

Namun sistem harus membedakan:

Known Fact
vs
Inferred Context
vs
Unknown

# 22. Context Clarification

Jika user berkata:

"Kasih advice untuk perkembangan bisnis dari data ini."

Tetapi sistem belum mengetahui bisnisnya:

AI harus bertanya terlebih dahulu.

Contoh informasi yang dibutuhkan:

- Perusahaan bergerak di bidang apa?
- Produk atau jasa apa yang dijual?
- Siapa target customer?
- Periode data?
- Apa tujuan utama bisnis?
- KPI apa yang paling penting?

# 23. Evidence-Based Business Advice

Setelah context cukup:

Business Context

- Spreadsheet Data
- Analytical Result
  ↓
  AI Reasoning
  ↓
  Objective Business Insight

AI harus membedakan:

## Data Fact

"Penjualan produk A meningkat 24%."

## Observation

"Pertumbuhan terbesar terjadi pada bulan Juli."

## Interpretation

"Pertumbuhan tersebut kemungkinan berkaitan dengan peningkatan
volume transaksi."

## Recommendation

"Bisnis dapat mempertimbangkan mempertahankan strategi yang
berkontribusi terhadap peningkatan tersebut."

Setiap level harus jelas.

# 24. Advice Confidence

Setiap insight dapat memiliki confidence / evidence level.

Contoh:

High Evidence
→ langsung terlihat dari data.

Moderate Evidence
→ terdapat pola tetapi membutuhkan konteks tambahan.

Low Evidence
→ hanya kemungkinan.

Unknown
→ data tidak cukup.

# 25. Visualization Engine

Python menghasilkan visualisasi berdasarkan analytical result.

Jenis chart:

- Bar chart
- Line chart
- Pie chart
- Area chart
- Scatter plot
- Histogram
- Box plot
- Heatmap
- Stacked bar
- Time-series chart

Pemilihan chart dapat dilakukan berdasarkan tipe data.

Contoh:

Time + Revenue
→ Line Chart

Category + Revenue
→ Bar Chart

Distribution
→ Histogram

Category + Category + Value
→ Heatmap / grouped visualization

# 26. Visualization Flow

User Request
↓
AI identifies analytical intent
↓
Python calculates data
↓
Visualization Engine selects chart
↓
Matplotlib / Seaborn generates visualization
↓
Chart metadata stored
↓
Next.js renders chart
↓
AI explains visualization

# 27. Automatic Dashboard

Setelah file selesai dianalisis,
sistem dapat membuat dashboard otomatis.

Dashboard berisi:

- KPI cards
- Revenue
- Transaction count
- Growth
- Top products
- Bottom products
- Trend
- Category distribution
- Important anomalies
- Data quality warning
- AI-generated insights

# 28. Interactive Data Explorer

Interactive Data Explorer merupakan salah satu
core interface Sheetsly.

User dapat melakukan analisis tanpa menggunakan AI.

Flow:

Sheet
↓
Table
↓
Column
↓
Operation
↓
Filter
↓
Grouping
↓
Comparison
↓
Visualization
↓
Result
↓
Source Trace

Contoh:

Sheet:
[ Penjualan ]

Table:
[ Sales Data ]

Operation:
[ Total ]

Column:
[ Revenue ]

Filter:
[ Month = July ]

Group By:
[ Product ]

Sort:
[ Highest → Lowest ]

Limit:
[ Top 10 ]

Visualization:
[ Bar Chart ]

[ Run Analysis ]

Hasil dikirim ke Python Analytical Engine.

UI tidak melakukan kalkulasi sendiri.

# 29. AI + Data Explorer

UI tidak hanya menyediakan chatbot.

User dapat:

1. Menggunakan UI secara manual.
2. Menggunakan AI.
3. Menggabungkan keduanya.

Contoh:

User memilih:

Sheet = Penjualan
Metric = Revenue
Group By = Produk

Kemudian meminta:

"Urutkan dari terbesar dan tampilkan hanya 5 teratas."

AI menerjemahkan request tersebut menjadi analytical instruction.

Python mengeksekusi.

UI memperbarui tabel dan chart.

AI dan Data Explorer harus menggunakan
analytical engine yang sama.

Contoh:

User menggunakan UI:

Sheet = Penjualan
Metric = Revenue
Group By = Produk

↓

Python menghasilkan hasil.

Kemudian user bertanya:

"Kenapa produk A paling tinggi?"

↓

AI menggunakan analytical result sebelumnya
sebagai context.

↓

Jika diperlukan AI meminta analytical engine
melakukan analisis tambahan.

↓

Python menghitung.

↓

AI menjelaskan berdasarkan hasil.

Sebaliknya:

User dapat memulai dari AI:

"Total revenue per produk."

↓

AI menghasilkan analytical instruction.

↓

UI secara otomatis dapat memperbarui:

Metric
Group By
Table
Chart

sehingga user dapat melihat
bagaimana AI menerjemahkan pertanyaannya
menjadi analisis.

# AI-Suggested Analysis

Setelah workbook selesai dianalisis,
Sheetsly dapat menghasilkan suggested analysis
berdasarkan struktur data yang ditemukan.

Contoh kategori:

## Data Overview

- Berapa total record?
- Berapa nilai total?
- Berapa kategori unik?

## Comparison

- Bagaimana performa antar periode?
- Wilayah mana yang paling tinggi?
- Produk mana yang paling rendah?

## Trend

- Bagaimana perubahan dari waktu ke waktu?
- Apakah terdapat peningkatan atau penurunan?

## Data Quality

- Apakah ada data kosong?
- Apakah ada duplikasi?
- Apakah terdapat nilai yang tidak valid?

## Business Investigation

- Apa perubahan terbesar?
- Apa anomali yang perlu diperiksa?
- Data apa yang perlu diperhatikan?

Suggested analysis harus berasal dari
kolom dan struktur data yang benar-benar tersedia.

AI tidak boleh membuat suggested question
berdasarkan kolom yang tidak ada.

# 30. Cross-Sheet Analysis

Sistem dapat menggunakan beberapa sheet.

Contoh:

Sheet Penjualan

- Sheet Produk
- Sheet Customer
- Sheet Cabang

          ↓

Relationship Detection

        ↓

Join / Merge

        ↓

Analysis

Sistem tidak boleh melakukan join hanya berdasarkan nama kolom
tanpa melakukan validasi relationship.

# 31. Relationship Detection

Potential relationship:

Product ID
Customer ID
Branch ID
Transaction ID
Date

Sistem melakukan:

- Column similarity
- Data overlap
- Cardinality analysis
- Identifier detection

Kemudian menentukan:

Confirmed Relationship
Potential Relationship
Unknown Relationship

# 32. Manual Relationship Configuration

Jika automatic detection tidak yakin,
user dapat menentukan relationship melalui UI.

Contoh:

Penjualan.Product ID
↓
Produk.Product ID

[ Confirm Relationship ]

# 33. Formula & Calculation Trace

# 33. Calculation & Operation Trace

Setiap hasil analisis harus memiliki calculation lineage.

Contoh:

User:
"Berapa total revenue bulan Juli?"

Sheetsly:

Operation:
SUM

Dataset:
Sales Data

Sheet:
Penjualan

Column:
Revenue

Filter:
Month = July

↓

Python execution

↓

Result:
Rp X

↓

Source Trace:

Sheet:
Penjualan

Range:
E2:E1284

Rows Used:
1,283

↓

UI:

Total Revenue
Rp X

[ How was this calculated? ]

Ketika user membuka "How was this calculated?",
Sheetsly menampilkan:

- Source sheet
- Source table
- Source range
- Source column
- Filter
- Operation
- Number of rows used
- Data quality status
- Calculation steps

Jika operasi melibatkan beberapa hasil:

Revenue
↓
Cost
↓
Profit
↓
Margin

setiap node memiliki lineage.

# Formula / Operation Reference

Sheetsly tidak bertujuan menjadi Excel replacement,
tetapi operation yang umum digunakan dalam Excel
harus dipetakan ke konsep analisis yang lebih sederhana.

Mapping awal:

SUM
→ Total

AVERAGE
→ Average

COUNT
→ Count

COUNTA
→ Count Filled

MIN
→ Lowest Value

MAX
→ Highest Value

SUMIF
→ Sum by Condition

SUMIFS
→ Sum by Multiple Conditions

COUNTIF
→ Count by Condition

COUNTIFS
→ Count by Multiple Conditions

IF
→ Conditional Value / Classification

AND
→ All Conditions Must Match

OR
→ Any Condition May Match

VLOOKUP
→ Lookup / Match

XLOOKUP
→ Lookup / Match

INDEX + MATCH
→ Advanced Lookup

FILTER
→ Filter Data

SORT
→ Sort Data

UNIQUE
→ Unique Values

PIVOT TABLE
→ Group + Aggregate + Pivot

Sheetsly tidak perlu meminta user
menulis formula tersebut.

Formula digunakan sebagai conceptual reference
untuk memetakan operasi yang umum dilakukan
oleh pengguna Excel ke operation engine Sheetsly.

# 34. Error Prevention

Jika sistem menemukan:

- Ambiguous orientation
- Invalid numeric values
- Missing required column
- Duplicate identifiers
- Broken relationship
- Insufficient data
- Unknown business context

Sistem harus:

STOP

bukan

GUESS

# 35. Analysis Result Object

Setiap analisis memiliki metadata:

- Query
- Intent
- Dataset
- Sheet
- Table
- Filters
- Grouping
- Calculation
- Result
- Source range
- Data quality status
- Confidence
- Visualization
- Explanation

# 36. Session Context

Percakapan AI menyimpan konteks analisis.

Contoh:

User:
"Berapa penjualan bulan Juli?"

AI:
"Rp120 juta."

User:
"Bandingkan dengan Juni."

Sistem memahami bahwa:

"Bandingkan"

merujuk pada metric dan dataset sebelumnya.

# 37. Multi-File Analysis

Tahap lanjutan dapat mendukung:

File A

- File B
- File C

Contoh:

Penjualan.xlsx
Inventory.xlsx
Customer.xlsx

        ↓

Unified Data Workspace

# 38. Export

User dapat menghasilkan:

- Excel
- CSV
- PDF
- Image
- Business report
- Dashboard snapshot

Hasil export harus berasal dari analytical engine,
bukan angka yang dibuat oleh AI.

# 39. Security & Privacy

Karena spreadsheet dapat berisi data sensitif:

- File isolation
- User authentication
- Access control
- Temporary processing
- Encryption
- Secure file deletion
- Dataset expiration
- Audit log

AI hanya boleh menerima data yang diperlukan untuk task tertentu,
bukan seluruh workbook secara otomatis.

# 40. Core Product Modules

## Module 1

File Management

## Module 2

Workbook Parser

## Module 3

Sheet Analyzer

## Module 4

Table Detection

## Module 5

Data Profiling

## Module 6

Data Quality

## Module 7

Schema & Relationship Detection

## Module 8

Spreadsheet Workspace

## Module 9

Data Explorer

## Module 10

Operation / Analysis Builder

## Module 11

Analytical Instruction Engine

## Module 12

Analytical Engine

## Module 13
Calculation Traceability

## Module 14
Source Traceability

## Module 15
AI Interface / Query Planner

## Module 16
AI Guardrail

## Module 17
Business Context Engine

## Module 18
Insight Engine

# 41. MVP Scope

MVP harus membuktikan bahwa Sheetsly dapat
mengubah spreadsheet menjadi interactive
analysis workspace.

## Phase 1 — Spreadsheet Foundation

1. Upload Excel
2. Workbook inspection
3. Sheet detection
4. Sheet metadata
5. Table detection
6. Vertical / horizontal orientation detection
7. Data profiling
8. Data quality warning
9. Actual spreadsheet viewer
10. Row / column identification
11. Cell / range traceability

## Phase 2 — Deterministic Analysis

12. Basic filtering
13. Sorting
14. SUM / Total
15. COUNT
16. AVERAGE
17. MIN
18. MAX
19. DISTINCT COUNT
20. GROUP BY
21. Basic comparison
22. Basic pivot operation
23. Basic conditional operations
24. Basic lookup / join
25. Calculation trace

## Phase 3 — Interactive Workspace

26. Analysis operation panel
27. Operation selector
28. Column selector
29. Filter builder
30. Grouping selector
31. Visualization selector
32. Result table
33. Result chart
34. Source trace panel
35. "How was this calculated?" interface

## Phase 4 — AI Interface

36. AI natural-language query
37. AI intent detection
38. AI analytical instruction generation
39. Instruction validation
40. Python deterministic execution
41. AI result explanation
42. AI hallucination guardrail
43. Business context clarification
44. Session context

## Phase 5 — AI + Workspace

45. AI modifies existing analysis
46. AI can generate filters
47. AI can generate grouping
48. AI can request visualization
49. UI reflects AI analytical instruction
50. User can continue AI-generated analysis manually

Fitur berikut dapat ditunda:

- Multi-file analysis
- Advanced forecasting
- Automated business recommendations
- Advanced statistical analysis
- Authentication
- Billing
- Advanced export
- Automated reporting

# 42. MVP User Flow

Landing Page
↓
Upload Spreadsheet
↓
Workbook Analysis
↓
Sheet Overview
↓
Data Quality Check
↓
Table Confirmation
↓
Interactive Workspace
↓
┌───────────────────────────────┐
│ │
│ Actual Data │
│ │
│ Sheet / Table / Cell / Range │
│ │
├───────────────────────────────┤
│ │
│ Analyze │
│ │
│ Calculate / Filter / Group / │
│ Compare / Lookup / Visualize │
│ │
├───────────────────────────────┤
│ │
│ AI Assistant │
│ │
│ Ask anything about your data │
│ │
└───────────────────────────────┘
↓
Analytical Instruction
↓
Python Analytical Engine
↓
Verified Result
↓
Table + Chart + Explanation
↓
Source / Calculation Trace
↓
User continues analysis
↓
Click / AI / Hybrid

# 43. Product Positioning

Bukan:

"AI untuk Excel."

Bukan:

"Chatbot untuk spreadsheet."

Bukan:

"Excel replacement."

Bukan:

"Dashboard generator."

Tetapi:

"AI-Assisted Spreadsheet Intelligence Workspace."

Core value:

Upload your data.
↓
See your actual data.
↓
Explore without knowing Excel.
↓
Analyze with clicks or natural language.
↓
Verify every result.
↓
Understand what your data is telling you.
↓
Discover what needs attention.

Primary Value Proposition:

Sheetsly helps people turn spreadsheet data
into understandable and actionable insight
without requiring advanced Excel or data analytics skills.

Secondary Value Proposition:

For experienced spreadsheet users,
Sheetsly accelerates repetitive analysis,
reporting, visualization, and exploration.

# Why Sheetsly

Sheetsly tidak bersaing hanya pada kemampuan
AI dalam memahami spreadsheet.

Nilai utama Sheetsly berasal dari integrasi:

Spreadsheet
+
Deterministic Data Engine
+
Interactive Workspace
+
Natural Language AI
+
Visualization
+
Traceability

Perbedaan utama:

## Chatbot

User:
"Analisis Excel saya."

↓

AI:
Memberikan jawaban.

## Sheetsly

User:
Upload Excel.

↓

Sheetsly:
Memahami workbook.

↓

User:
Melihat actual data.

↓

Sheetsly:
Menunjukkan struktur dan data quality.

↓

User:
Memilih analysis melalui UI
atau bertanya kepada AI.

↓

Python:
Menghitung secara deterministic.

↓

Sheetsly:
Menampilkan result + chart + source.

↓

User:
Dapat memeriksa bagaimana hasil diperoleh.

Sheetsly bukan hanya tempat untuk
bertanya kepada AI.

Sheetsly adalah workspace untuk bekerja
dengan data spreadsheet.

# Core Product Loop

Setiap interaksi Sheetsly mengikuti loop:

OBSERVE
↓
UNDERSTAND
↓
ANALYZE
↓
VERIFY
↓
EXPLAIN
↓
ACT

## Observe

User melihat actual spreadsheet data.

## Understand

System memahami struktur,
schema, data type, relationship,
dan data quality.

## Analyze

User menggunakan:

- Click-based operation
- AI query
- Hybrid interaction

## Verify

Python menjadi source of truth.

Result memiliki source trace
dan calculation lineage.

## Explain

AI menjelaskan hasil
menggunakan verified result.

## Act

User menggunakan insight
untuk melakukan tindakan,
investigasi, atau analisis lanjutan.


# 44. Core Product Philosophy

Spreadsheet provides the evidence.

Python calculates and validates.

The Analytical Engine provides deterministic results.

UI makes data exploration understandable.

AI provides the natural-language interface.

AI explains verified results.

User provides the business context.

The system asks when it does not know.

The system never guesses when the data can be checked.

# 45. Long-Term Direction

Platform dapat berkembang menjadi:

AI Business Intelligence Platform

yang memungkinkan user:

- Upload spreadsheet
- Connect database
- Connect API
- Connect POS
- Connect accounting system
- Connect e-commerce
- Monitor KPI
- Generate dashboard
- Ask business questions
- Detect anomalies
- Forecast performance
- Generate reports
- Receive automated recommendations

# 46. Final Architecture

USER
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Direct Interaction          Natural Language
             │                           │
             ▼                           ▼
       Next.js Workspace          AI Assistant
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 Analytical Instruction
                           │
                           ▼
                    FastAPI Backend
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
   Workbook Engine   Analytical Engine   AI Orchestrator
          │                │                 │
          │                ▼                 │
          │          Python Processing       │
          │                │                 │
          │        ┌───────┴────────┐        │
          │        │                │        │
          ▼        ▼                ▼        ▼
      OpenPyXL   Pandas         Matplotlib   LLM
                  /Polars       /Seaborn
          │        │                │        │
          └────────┴────────┬───────┴────────┘
                            ▼
                     Verified Result
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
          ▼                 ▼                  ▼
       Table              Chart             Insight
          │                 │                  │
          └─────────────────┼──────────────────┘
                            ▼
                    Source / Trace Layer
                            │
                            ▼
                    Next.js Workspace
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         Actual Data     Analysis       AI Chat
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                      Next Interaction
# 47. Fundamental Rule

The system should never answer:

"I think the answer is..."

when the data engine can determine the answer.

The system should never answer:

"The company probably..."

when the business context is unknown.

The system should instead:

1. Inspect the data.
2. Validate the structure.
3. Identify uncertainty.
4. Ask the user when necessary.
5. Calculate using Python.
6. Trace the result to the source.
7. Let AI explain the verified result.
8. Clearly distinguish fact, observation, inference, and recommendation.
9. AI-generated analytical instruction must be validated
   before execution.
10. UI-generated analytical instruction and AI-generated
    analytical instruction must use the same analytical engine.
11. The same analysis must produce the same deterministic
    result regardless of whether it was initiated through
    UI or AI, assuming identical input and parameters.
12. The system must never silently change the dataset,
    filter, column, operation, or grouping used for analysis.
13. Every generated result must expose sufficient metadata
    to reproduce or verify the analysis.
14. When structural confidence is insufficient,
    the system must ask the user instead of guessing.

# 48. Product Identity

Core concept:

"Turn spreadsheets into understandable,
interactive, and evidence-based insights."

Sheetsly is:

An AI-Assisted Spreadsheet Intelligence Workspace.

Sheetsly combines:

- Actual Spreadsheet Data
- Deterministic Data Processing
- Interactive Data Exploration
- Click-Based Analysis
- Natural Language Analysis
- Automated Visualization
- Source Traceability
- Calculation Traceability
- Evidence-Based Business Insight

Sheetsly is NOT:

- An Excel replacement.
- Merely an AI chatbot.
- Merely a dashboard generator.
- A system that lets AI freely manipulate data.
- A system that guesses missing information.

Sheetsly is:

Workspace
+
Analytical Engine
+
AI Interface
+
Evidence
+
Visualization
+
Traceability

Core principle:

AI understands.

Python calculates.

The analytical engine verifies.

The spreadsheet provides evidence.

The user provides business context.

The workspace makes the entire process understandable.

# Architecture Principle: One Engine, Multiple Interfaces

Sheetsly harus memiliki satu analytical engine
yang digunakan oleh seluruh interface.

Tidak boleh terdapat:

UI Calculation Engine
dan
AI Calculation Engine

yang berjalan secara terpisah.

Arsitektur yang benar:

                 UI
                  │
                  ▼
        Analytical Instruction
                  ▲
                  │
                 AI
                  │
                  ▼
        ┌───────────────────┐
        │ Analytical Engine │
        │      Python       │
        └─────────┬─────────┘
                  │
                  ▼
             Verified Result

Dengan prinsip:

Different Interfaces
→ Same Instruction Model
→ Same Analytical Engine
→ Same Result
→ Same Traceability


# Operation / Analysis Builder

Operation Builder bertugas mengubah pilihan user
menjadi analytical instruction.

Contoh:

User memilih:

Operation:
Total

Column:
Revenue

Filter:
Region = Serang

↓

Operation Builder:

{
    Operation: SUM
    Column: Revenue
    Filter:
        Region = Serang
}

↓

Analytical Engine

Operation Builder tidak melakukan kalkulasi.

Operation Builder hanya membangun
instruction yang akan dieksekusi
oleh Analytical Engine.

# AI + Operation Builder

AI dapat menghasilkan instruction
yang sama dengan Operation Builder.

Contoh:

User:
"Berapa total revenue di Serang?"

AI:

Operation:
SUM

Column:
Revenue

Filter:
Region = Serang

↓

Operation Builder / Instruction Validator

↓

Analytical Engine

↓

Result

Dengan demikian:

Click UI
dan
AI

dapat menghasilkan analytical instruction
yang kompatibel dengan engine yang sama.

# 49. Current Project State

Current project structure:

sheetsly/
│
├── sheetsly_frontend/
│   └── Next.js
│
└── sheetsly_backend/
    └── FastAPI

Current implementation status:

- Project root created.
- Next.js frontend initialized.
- FastAPI backend directory created.
- Backend architecture has not yet been fully implemented.
- Analytical engine has not yet been implemented.
- Spreadsheet ingestion has not yet been implemented.
- AI integration has not yet been implemented.
- Workspace UI has not yet been implemented.

Initial implementation priority:

1. Establish FastAPI backend.
2. Establish Next.js frontend.
3. Implement spreadsheet upload.
4. Implement workbook inspection.
5. Implement sheet detection.
6. Implement actual spreadsheet viewer.
7. Implement table and orientation detection.
8. Implement deterministic analytical engine.
9. Implement operation builder.
10. Implement basic visualization.
11. Implement source and calculation traceability.
12. Implement AI query planner.
13. Implement AI + analytical engine integration.
14. Implement hybrid workspace interaction.

Python version: 3.12.0
Nextjs version: 16.2.6