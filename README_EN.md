# ViSGKCap: An Accessibility-First Vietnamese Textbook Captioning Dataset
[![Dataset](https://img.shields.io/badge/Dataset-bbdontcry%2FViSGKCap-blue?logo=huggingface)](https://huggingface.co/datasets/bbdontcry/ViSGKCap)

[Vietnamese](README.md) | English

This repository implements a pipeline for building a **Vietnamese image captioning dataset** from [Vietnamese primary-school textbooks](https://sachgiaokhoa.online/) in the **Canh Dieu** collection. The project follows an **accessibility-first** direction: each page image is described with two caption levels, **short** and **detail**.

Full report available at: [`docs/report.pdf`](docs/report.pdf).

> Goal: make the full data creation pipeline reproducible, from PDF textbooks to final JSON/JSONL dataset files.

---

<p align="center">
  <img src="./images/captioning-pipeline.png" alt="Pipeline overview: PDF to PNG to Gemini captions to CSV to Supabase annotation and QC to postprocessing to JSON and JSONL" width="1000" />
</p>

## Table of Contents

- [Tutorial Video](#tutorial-video)
- [1. Final Dataset Schema](#1-final-dataset-schema)
- [2. Textbooks in Scope](#2-textbooks-in-scope)
- [3. Repository Structure](#3-repository-structure)
- [4. Environment Setup](#4-environment-setup)
  - [4.1. Option A - Conda Environment](#41-option-a---conda-environment)
  - [4.2. Option B - Virtual Environment and Pip](#42-option-b---virtual-environment-and-pip)
  - [4.3. System Requirement for Stage 0](#43-system-requirement-for-stage-0)
- [5. Secrets Configuration](#5-secrets-configuration)
- [6. Reproducing the Pipeline](#6-reproducing-the-pipeline)
  - [Stage 0: PDF to PNG](#stage-0-pdf-to-png)
  - [Stage 1: Gemini Captioning](#stage-1-gemini-captioning)
  - [Stage 2: XLSX to Supabase Import CSV](#stage-2-xlsx-to-supabase-import-csv)
  - [Supabase: Import, Human Annotation/QC, Export](#supabase-import-human-annotationqc-export)
  - [Stage 3: Postprocess to Final JSON/JSONL](#stage-3-postprocess-to-final-jsonjsonl)
- [7. Required Metadata Catalog](#7-required-metadata-catalog)
- [8. Troubleshooting](#8-troubleshooting)
- [9. Notes](#9-notes)

---

## 1. Final Dataset Schema

Each sample represents **one textbook page image**:

```json
{
  "id": "SGK_CanhDieu_DaoDuc_1_page_001",
  "image": "SGK_CanhDieu_DaoDuc_1_page_001.png",
  "metadata": {
    "Type": "SGK",
    "Collection": "Canh Dieu",
    "Title": "Dao duc 1",
    "Grade": 1,
    "Subject": "Dao duc",
    "Volume": "",
    "Author": "...",
    "Publisher": "..."
  },
  "caption_short": "A concise description of the page image...",
  "caption_detail": "A detailed, listening-flow description of the page image..."
}
```

- **`caption_short`**: a brief, general page description.
- **`caption_detail`**: a detailed accessibility-oriented description. If the page contains text or tables, visible text should be integrated into the description as contextualized inline OCR.
- **`metadata`**: looked up from [`metadata_catalog.csv`](data/stage3_inputs/metadata_catalog.csv) using **longest prefix match**. The postprocessing stage does not rely on default metadata.

Final outputs are written to:

- [`output/stage3_processed_dataset/dataset_final.json`](output/stage3_processed_dataset/dataset_final.json)
- [`output/stage3_processed_dataset/dataset_final.jsonl`](output/stage3_processed_dataset/dataset_final.jsonl)

---

## 2. Textbooks in Scope

The current scope contains **10 textbooks** from grades 1 to 3 in the **Canh Dieu** collection:

- **Grade 1:** Ethics, Nature and Society, Mathematics
- **Grade 2:** Ethics, Nature and Society, Vietnamese Language Volume 1, Vietnamese Language Volume 2
- **Grade 3:** Ethics, Nature and Society, Mathematics Volume 1

---

## 3. Repository Structure

```
vn-textbook-caption-dataset
├── data
│   ├── raw/                         # Original PDF textbooks
│   ├── processed/                   # PNG page images from Stage 0
│   └── stage3_inputs/               # Inputs for Stage 3
│       ├── metadata_catalog.csv
│       └── supabase_export.csv
├── output
│   ├── stage1_generated_captions/   # stage1_*.xlsx, one file per book
│   ├── stage2_supabase_input/       # stage2_supabase_input.csv
│   └── stage3_processed_dataset/    # dataset_final.json/jsonl
├── prompts/                         # core + adapters
├── supabase-schema.sql              # schema table + enums
└── notebooks/                       # Stage0/1/2/3
```

> Note on **relative paths**: the stage notebooks use paths such as `Path("../data/...")` by default. Keep the notebooks in `notebooks/` and run them from there. If you move a notebook to the repository root, update the paths in its `CONFIG` cell.

---

## 4. Environment Setup

This repository supports two setup options:

- **Option A (recommended):** create a Conda environment from [`nlp-captioning.yml`](nlp-captioning.yml)
- **Option B:** create a Python virtual environment and install dependencies with pip

### 4.1. Option A - Conda Environment

Create and activate the environment:

```bash
conda env create -f nlp-captioning.yml
conda activate nlp-captioning
```

If you use **Jupyter Notebook/Lab**, register the environment as a kernel:

```bash
python -m ipykernel install --user --name nlp-captioning --display-name "nlp-captioning"
```

### 4.2. Option B - Virtual Environment and Pip

Python **3.10+** is recommended.

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
source .venv/bin/activate

pip install -U pip
pip install pandas openpyxl tqdm pillow pdf2image python-dotenv google-generativeai
```

If you run the notebooks locally, install JupyterLab as well:

```bash
pip install jupyterlab
```

### 4.3. System Requirement for Stage 0

Stage 0 uses `pdf2image`, which requires **Poppler**.

- Ubuntu/Debian:

  ```bash
  sudo apt-get update
  sudo apt-get install -y poppler-utils
  ```

- macOS with Homebrew:

  ```bash
  brew install poppler
  ```

- Windows:

  ```bash
  conda install -c conda-forge poppler
  ```

  Alternatively, install Poppler manually and add it to `PATH`, or run Stage 0 on Colab:

  ```bash
  !apt-get install -y poppler-utils
  ```

---

## 5. Secrets Configuration

Create a `.env` file at the repository root:

```env
# Gemini API Key
GEMINI_API_KEY=YOUR_KEY_HERE
```

Stage 1 loads the key with:

```python
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
```

---

## 6. Reproducing the Pipeline

### Stage 0: PDF to PNG

- **Notebook:** [`notebooks/Stage0_pdf2png.ipynb`](notebooks/Stage0_pdf2png.ipynb)
- **Input:** `data/raw/*.pdf`
- **Output:** `data/processed/*.png`

Image naming convention:

```text
SGK_<Collection>_<BookTitle>_<Grade>_<Volume?>_<Page>
```

If a book has no volume, omit the volume segment. Example:

```text
SGK_CanhDieu_DaoDuc_1_page_001
```

If you run this stage on Colab, install `poppler-utils` before using `pdf2image`.

---

### Stage 1: Gemini Captioning

- **Notebook:** [`notebooks/Stage1_Gemini_Captioning.ipynb`](notebooks/Stage1_Gemini_Captioning.ipynb)
- **Input:** `data/processed/*.png` filtered by `PREFIX`, plus prompts from `prompts/`
- **Output:** `output/stage1_generated_captions/stage1_<PREFIX>.xlsx`

Set the target book prefix in the notebook:

```python
PREFIX = BOOK_PREFIXES[i]
```

Useful settings:

- `NUM_IMAGES=5` for a quick test run
- `RESUME_IF_EXISTS=True` to resume after rate limits or interruptions
- `SAVE_EVERY=10` to autosave every 10 images

---

### Stage 2: XLSX to Supabase Import CSV

- **Notebook:** [`notebooks/Stage2_XLSX_to_Supabase_CSV.ipynb`](notebooks/Stage2_XLSX_to_Supabase_CSV.ipynb)
- **Input:** `output/stage1_generated_captions/stage1_*.xlsx`
- **Output:** [`output/stage2_supabase_input/stage2_supabase_input.csv`](output/stage2_supabase_input/stage2_supabase_input.csv)

This stage merges generated caption files and converts array-like fields into a format suitable for Supabase/Postgres import.

---

### Supabase: Import, Human Annotation/QC, Export

1. Create a Supabase project.
2. Open the SQL editor and run [`supabase-schema.sql`](supabase-schema.sql) to create the required enums and the `public.dataset` table.
3. Import [`stage2_supabase_input.csv`](output/stage2_supabase_input/stage2_supabase_input.csv) into `public.dataset`.
4. Perform human annotation/QC in the team's web UI: edit captions, set `is_checked` to `checked` or `reviewed`, add `error_tags`, and write change logs when needed.
5. Export `public.dataset` as CSV from Supabase.

Place the exported file at:

- [`data/stage3_inputs/supabase_export.csv`](data/stage3_inputs/supabase_export.csv)

Annotation rules are documented in [`docs/annotation_guideline.md`](docs/annotation_guideline.md).

---

### Stage 3: Postprocess to Final JSON/JSONL

- **Notebook:** [`notebooks/Stage3_Postprocess.ipynb`](notebooks/Stage3_Postprocess.ipynb)
- **Inputs:**
  - [`data/stage3_inputs/supabase_export.csv`](data/stage3_inputs/supabase_export.csv)
  - [`data/stage3_inputs/metadata_catalog.csv`](data/stage3_inputs/metadata_catalog.csv)
- **Outputs:**
  - [`output/stage3_processed_dataset/dataset_final.json`](output/stage3_processed_dataset/dataset_final.json)
  - [`output/stage3_processed_dataset/dataset_final.jsonl`](output/stage3_processed_dataset/dataset_final.jsonl)

---

## 7. Required Metadata Catalog

- **File:** [`data/stage3_inputs/metadata_catalog.csv`](data/stage3_inputs/metadata_catalog.csv)
- The `prefix` column must match sample `id` prefixes.
- Stage 3 uses **longest prefix match** to attach metadata to each sample.
- UTF-8-SIG is recommended if the CSV will be opened in Excel.

---

## 8. Troubleshooting

**Path not found**

- Run notebooks from the expected working directory, preferably `notebooks/`.
- If you run from another directory, update the relevant `Path("../...")` values.

**Supabase CSV import fails because of enum or array columns**

- Stage 2 converts array columns to Postgres array literals such as `{}` or `{"a","b"}`.
- Check enum columns such as `page_type`, `review_priority`, and `is_checked` against the allowed values in [`supabase-schema.sql`](supabase-schema.sql).

**Gemini rate limits or network errors**

- Set `RESUME_IF_EXISTS=True`.
- Keep `SAVE_EVERY` small.
- Use a smaller `NUM_IMAGES` for test runs.
- Increase `MAX_RETRY` or `BASE_DELAY_SEC` if needed.

---

## 9. Notes

- Annotation guideline: [`docs/annotation_guideline.md`](docs/annotation_guideline.md)
- This repository is intended for academic/coursework use. Make sure the textbook materials are used according to the requirements of your course, institution, and applicable content policies.
