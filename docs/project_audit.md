# Project Audit: Public Academic Release Readiness

This audit records repository consistency, reproducibility, and data-hygiene items for preparing ViSGKCap as an academic public repository.

## Current Source of Truth

- Canonical Supabase export: `data/stage3_inputs/supabase_export_full.csv`
- Final dataset outputs: `output/stage3_processed_dataset/dataset_final.json` and `output/stage3_processed_dataset/dataset_final.jsonl`
- Current snapshot: 1,237 samples, 1,237 processed PNG images, and 10 textbook PDFs.
- Data artifact policy: large inputs and generated outputs are tracked with DVC pointer files, not direct Git blobs.
- `CV_DATA_NOTE.md` is a CV-specific note and is not the dataset-count source of truth for the repository.

## Findings

### P0 Release Blockers

- **Large data was partly Git-tracked directly.** Original PDFs and the Supabase export were tracked by Git; generated `output/` was untracked. These artifacts are now represented by DVC pointer files.
- **Stage 3 export filename was inconsistent.** README and the notebook referred to a legacy shorter Supabase export filename, while the actual canonical file is `supabase_export_full.csv`. Documentation and notebook config now use the canonical filename.
- **Notebook outputs leaked machine-local state.** Some notebooks contained executed outputs, base64 image payloads, and absolute Windows paths. Notebook outputs have been cleared.

### P1 Professional Polish

- **DVC credentials are owner-specific.** The default DagsHub remote URL is tracked in `.dvc/config`, but authentication must stay local via `dvc remote modify dagshub --local ...`.
- **Public data rights need careful wording.** The repo should remain framed as academic/coursework use unless textbook redistribution rights are explicitly confirmed.
- **README parity matters.** Vietnamese and English READMEs should keep the same dataset count, canonical paths, DVC instructions, and academic-use note.

### P2 Nice-to-Have Improvements

- Add a lightweight validation notebook or script later to check image/file/schema consistency without re-running Gemini.
- Consider creating a Hugging Face dataset card that mirrors the same count, usage note, and DVC/Hugging Face relationship.
- Consider adding a short `docs/data_contract.md` if more teams consume the exported JSON/JSONL.

## Validation Checklist

- `git status --short` should show DVC pointer files and documentation changes, not raw data blobs staged as normal Git files.
- `dvc status` should report the DVC workspace as clean after all artifacts are present.
- `rg -n "supabase_export[.]csv|D:\\\\|OneDrive|image/png" README*.md notebooks` should not report stale mandatory paths or notebook output payloads.
- Count checks should confirm:
  - PNG count in `data/processed/` equals final JSON sample count.
  - Every final JSON `image` exists in `data/processed/`.
  - Every final JSON `id` matches a `metadata_catalog.csv` prefix by longest-prefix lookup.
  - Prompt controlled vocab and `supabase-schema.sql` enum values stay aligned.

## Change Rules Going Forward

- Do not commit generated PNG, XLSX, CSV, JSON, or PDF data blobs directly to Git unless the data policy changes.
- Keep DVC credentials out of the repo; use `.dvc/config.local` or environment variables.
- If the dataset count changes, update both READMEs, this audit file, and any public dataset card in the same change.
- If the Supabase export filename changes again, update Stage 3 notebook config, README VN/EN, and DVC tracking together.
