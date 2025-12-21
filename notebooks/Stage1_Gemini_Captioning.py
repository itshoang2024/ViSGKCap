# %% [markdown]
# # STAGE 1: GEMINI CAPTIONING — Accessibility-first (Inline OCR contextualized)
# Chạy 1 quyển / 1 lần. Output: 1 file Excel cho 1 quyển (PREFIX).
# 
# **Guideline:**
# - Không suy luận giáo dục/đạo đức
# - Bắt buộc 2 caption: caption_short (mô chung chung) + caption_detail (thuyết minh theo luồng nghe, inline OCR)
# - OCR trả về phải đầy đủ nguyên văn như trong ảnh, không tóm tắt ý, không diễn giải, suy luận
# - ... (Xem chi tiết trong báo cáo)

# %% [markdown]
# ## 1. CẤU HÌNH

# %%
%pip install -q google-generativeai pillow tqdm pandas openpyxl

# %%
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from PIL import Image
from tqdm import tqdm
import google.generativeai as genai

# ================== THAY ĐỔI CẤU HÌNH TẠI ĐÂY ==================
BOOK_PREFIXES = [
    "SGK_CanhDieu_DaoDuc_1",            # 0
    "SGK_CanhDieu_DaoDuc_2",            # 1
    "SGK_CanhDieu_DaoDuc_3",            # 2

    "SGK_CanhDieu_TiengViet_2_Tap1",    # 3
    "SGK_CanhDieu_TiengViet_2_Tap2",    # 4

    "SGK_CanhDieu_Toan_1",              # 5
    "SGK_CanhDieu_Toan_3_Tap1",         # 6
    
    "SGK_CanhDieu_TuNhienVaXaHoi_1",    # 7
    "SGK_CanhDieu_TuNhienVaXaHoi_2",    # 8
    "SGK_CanhDieu_TuNhienVaXaHoi_3",    # 9
]
PREFIX = BOOK_PREFIXES[0]  # <-- đổi theo quyển cần chạy

IMAGE_DIR = "../data/processed"
OUTPUT_DIR = "../output/stage1"
PROMPT_DIR = "../prompts"

CORE_PROMPT_FILE = "core.txt"
ADAPTER_TEXT_FILE = "adapter_textheavy.txt"
ADAPTER_MATH_FILE = "adapter_math.txt"
ADAPTER_ILLUSTRATION_FILE = "adapter_illustration.txt"

# "auto" (khuyến nghị) hoặc "textheavy" / "math" / "illustration"
ADAPTER_MODE = "auto"

# Output 1 quyển / 1 file
OUTPUT_EXCEL = os.path.join(OUTPUT_DIR, f"stage1_{PREFIX}.xlsx")

# Chạy test nhanh: đặt NUM_IMAGES=5; chạy full: NUM_IMAGES=None
NUM_IMAGES: Optional[int] = None

# Tự resume nếu đã có file output (khuyến nghị bật vì có thể gặp rate limit)
RESUME_IF_EXISTS = True

# Lưu tạm sau mỗi N ảnh để tránh mất dữ liệu khi lỗi
SAVE_EVERY = 10

# Retry settings
MAX_RETRY = 6
BASE_DELAY_SEC = 8

# %%
os.makedirs(OUTPUT_DIR, exist_ok=True)

def detect_adapter(prefix: str) -> str:
    p = prefix.lower()
    if "tiengviet" in p:
        return "textheavy"
    if "toan" in p:
        return "math"
    return "illustration"

def load_prompt(prompt_dir: str, core_file: str, adapter_mode: str, prefix: str) -> Tuple[str, str]:
    core_path = os.path.join(prompt_dir, core_file)
    with open(core_path, "r", encoding="utf-8") as f:
        core = f.read().strip()

    mode = adapter_mode
    if mode == "auto":
        mode = detect_adapter(prefix)

    if mode == "textheavy":
        adapter_file = ADAPTER_TEXT_FILE
    elif mode == "math":
        adapter_file = ADAPTER_MATH_FILE
    elif mode == "illustration":
        adapter_file = ADAPTER_ILLUSTRATION_FILE
    else:
        raise ValueError(f"ADAPTER_MODE không hợp lệ: {adapter_mode}")

    adapter_path = os.path.join(prompt_dir, adapter_file)
    with open(adapter_path, "r", encoding="utf-8") as f:
        adapter = f.read().strip()

    system_prompt = core + "\n\n" + adapter
    return system_prompt, mode

SYSTEM_PROMPT, ADAPTER_USED = load_prompt(PROMPT_DIR, CORE_PROMPT_FILE, ADAPTER_MODE, PREFIX)

print(f"✓ PREFIX: {PREFIX}")
print(f"✓ Adapter used: {ADAPTER_USED}")
print(f"✓ Output: {OUTPUT_EXCEL}")

# %% [markdown]
# ## 2. KHỞI TẠO GEMINI API

# %%
from dotenv import load_dotenv
load_dotenv() 

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="models/gemini-3-pro-preview",
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    },
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ],
)

print("✓ Gemini model initialized")

# %% [markdown]
# ## 3. DANH SÁCH ẢNH

# %%
image_files = sorted([
    f for f in os.listdir(IMAGE_DIR)
    if f.startswith(PREFIX) and f.lower().endswith(".png")
])

print(f"✓ Found {len(image_files)} images")
print("First 5 images:")
for i, fname in enumerate(image_files[:5], 1):
    print(f"  {i}. {fname}")

# %% [markdown]
# ## 4. HÀM TIỆN ÍCH: PARSE + VALIDATE JSON

# %%
ALLOWED_PAGE_TYPES = {"cover","title_page","toc","content","exercise","blank","other"}
ALLOWED_REVIEW_PRIORITY = {"low","normal","high"}
ALLOWED_AUTO_FLAGS = {
    "OCR_UNREADABLE","OCR_LONG","HAS_TABLE","LAYOUT_COMPLEX",
    "POSSIBLE_BLANK","LOW_CERTAINTY",
    "COUNTING_UNCERTAIN","COUNTING_WRONG",
    "CLOCK_READING_UNCERTAIN","CLOCK_READING_WRONG",
}
ALLOWED_OBJECTS = {
    # People
    "person_child","person_adult","student","teacher",
    # Animals
    "animal_generic","animal_pet","animal_farm","animal_wild",
    # Food / countable
    "food_fruit","food_vegetable","food_bundle",
    # School items
    "book","notebook","pen","pencil","school_bag",
    # Math / time
    "clock_analog","clock_digital","countable_object","grouped_object",
    # Others
    "table","chart","illustration_scene",
}

def _extract_json_object(text: str) -> Optional[str]:
    """
    Trích object JSON đầu tiên trong text nếu Gemini lỡ trả thêm ký tự.
    Dùng stack đếm ngoặc {} để lấy substring hợp lệ.
    """
    if not text:
        return None
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

def _to_bool(x: Any) -> Optional[bool]:
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("true","yes","1"):
            return True
        if s in ("false","no","0"):
            return False
    if isinstance(x, (int, float)):
        if x == 1:
            return True
        if x == 0:
            return False
    return None

def _normalize_auto_flags(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        flags = [str(i).strip() for i in x if str(i).strip()]
    elif isinstance(x, str):
        s = x.strip()
        # thử parse JSON list nếu có
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                if isinstance(arr, list):
                    flags = [str(i).strip() for i in arr if str(i).strip()]
                else:
                    flags = []
            except Exception:
                # fallback split
                flags = [p.strip() for p in s.strip("[]").split(",") if p.strip()]
        else:
            # split theo ; hoặc ,
            sep = ";" if ";" in s else ","
            flags = [p.strip() for p in s.split(sep) if p.strip()]
    else:
        flags = [str(x).strip()] if str(x).strip() else []

    # lọc theo allow-list + giữ LOW_CERTAINTY nếu phát hiện lỗi
    out = []
    for f in flags:
        if f in ALLOWED_AUTO_FLAGS and f not in out:
            out.append(f)
    return out

def _normalize_objects(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        objs = [str(i).strip() for i in x]
    elif isinstance(x, str):
        objs = [p.strip() for p in x.split(",")]
    else:
        return []

    return [o for o in objs if o in ALLOWED_OBJECTS]

def validate_and_normalize(g: Dict[str, Any]) -> Dict[str, Any]:
    """
    Đảm bảo output đủ key, đúng kiểu, giá trị trong domain cho QA.
    Nếu thiếu/sai, tự fill default và gắn LOW_CERTAINTY.
    """
    out: Dict[str, Any] = {}

    out["schema_version"] = str(g.get("schema_version", "cd_caption_v12")).strip() or "cd_caption_v12"

    page_type = str(g.get("page_type", "other")).strip()
    if page_type not in ALLOWED_PAGE_TYPES:
        page_type = "other"
        out.setdefault("auto_flags", [])
        out["notes"] = (str(g.get("notes","")) + " | page_type invalid").strip(" |")
    out["page_type"] = page_type

    text_in_image = g.get("text_in_image", "")
    out["text_in_image"] = str(text_in_image) if text_in_image is not None else ""

    # booleans
    has_text = _to_bool(g.get("has_text"))
    has_table = _to_bool(g.get("has_table"))

    # heuristics
    if has_text is None:
        has_text = bool(out["text_in_image"].strip())
    out["has_text"] = has_text

    auto_flags = _normalize_auto_flags(g.get("auto_flags"))
    # nếu has_table None, suy ra từ auto_flags hoặc từ text (nhẹ)
    if has_table is None:
        has_table = ("HAS_TABLE" in auto_flags)
    out["has_table"] = has_table if has_table is not None else False

    objects = _normalize_objects(g.get("objects_present"))
    out["objects_present"] = objects

    caption_short = g.get("caption_short", "")
    out["caption_short"] = str(caption_short) if caption_short is not None else ""

    caption_detail = g.get("caption_detail", "")
    out["caption_detail"] = str(caption_detail) if caption_detail is not None else ""

    review_priority = str(g.get("review_priority", "normal")).strip()
    if review_priority not in ALLOWED_REVIEW_PRIORITY:
        review_priority = "normal"

    # heuristic nâng priority
    if out["has_table"] or ("OCR_UNREADABLE" in auto_flags) or ("LAYOUT_COMPLEX" in auto_flags):
        review_priority = "high"
    if page_type == "blank" or ("POSSIBLE_BLANK" in auto_flags):
        review_priority = "low"

    # heuristic OCR_LONG
    if len(out["text_in_image"]) > 1200 and "OCR_LONG" not in auto_flags:
        auto_flags.append("OCR_LONG")
        review_priority = "high"

    out["review_priority"] = review_priority

    notes = g.get("notes", "")
    out["notes"] = str(notes) if notes is not None else ""

    # ensure flags are valid
    out["auto_flags"] = [f for f in auto_flags if f in ALLOWED_AUTO_FLAGS]

    # if missing important fields, mark LOW_CERTAINTY
    missing = []
    for k in ["caption_short","caption_detail"]:
        if not out[k].strip():
            missing.append(k)
    if missing:
        if "LOW_CERTAINTY" not in out["auto_flags"]:
            out["auto_flags"].append("LOW_CERTAINTY")
        out["review_priority"] = "high"
        out["notes"] = (out["notes"] + f" | missing {','.join(missing)}").strip(" |")

    return out

# %% [markdown]
# ## 5. HÀM GỌI GEMINI API (RETRY + PARSE)

# %%
def call_gemini_api(image_path: str, max_retry: int = MAX_RETRY, base_delay: int = BASE_DELAY_SEC) -> Optional[Dict[str, Any]]:
    img = Image.open(image_path).convert("RGB")

    for attempt in range(max_retry):
        try:
            resp = model.generate_content(contents=[SYSTEM_PROMPT, img])
            raw = (resp.text or "").strip()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                extracted = _extract_json_object(raw)
                if not extracted:
                    raise
                data = json.loads(extracted)

            if not isinstance(data, dict):
                raise ValueError("Gemini output is not a JSON object")

            return validate_and_normalize(data)

        except Exception as e:
            err = str(e)

            if "429" in err or "TooManyRequests" in err:
                wait = base_delay + attempt * 6
                print(f"    ⚠ 429 Rate limit — sleep {wait}s (attempt {attempt+1}/{max_retry})")
                time.sleep(wait)
                continue

            # JSON parse / validation error -> retry nhẹ 1-2 lần
            if attempt < max_retry - 1:
                wait = 2 + attempt * 2
                print(f"    ⚠ Error — retry in {wait}s (attempt {attempt+1}/{max_retry}): {err[:120]}")
                time.sleep(wait)
                continue

            print(f"    ✗ Failed: {err[:200]}")
            return None

    return None

# %% [markdown]
# ## 6. PROCESS TẤT CẢ ẢNH (1 QUYỂN / 1 LẦN)

# %%
COLUMN_ORDER = [
    "id",
    "image",
    "page_type",
    "has_text",
    "has_table",
    "objects_present",
    "caption_short",
    "caption_detail",
    "text_in_image",
    "review_priority",
    "auto_flags",
    "notes",
    "is_checked",
    "error_tags",
    "change_log",
]

def load_existing_rows(output_excel: str) -> Tuple[List[Dict[str, Any]], set]:
    if not (RESUME_IF_EXISTS and os.path.exists(output_excel)):
        return [], set()
    try:
        df = pd.read_excel(output_excel)
        rows = df.to_dict(orient="records")
        done = set(df["id"].astype(str).tolist()) if "id" in df.columns else set()
        print(f"✓ Resume enabled: loaded {len(rows)} rows from existing file")
        return rows, done
    except Exception as e:
        print(f"⚠ Could not read existing output for resume: {e}")
        return [], set()

def rows_to_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    # đảm bảo đủ cột
    for c in COLUMN_ORDER:
        if c not in df.columns:
            df[c] = "" if c not in ("has_text","has_table","has_illustration") else False
    df = df[COLUMN_ORDER]
    return df

def save_rows_to_excel(rows: List[Dict[str, Any]], path: str) -> None:
    df = rows_to_dataframe(rows)

    # normalize auto_flags to readable string
    df["auto_flags"] = df["auto_flags"].apply(
        lambda x: ";".join(x) if isinstance(x, list) else ("" if pd.isna(x) else str(x))
    )
    df["objects_present"] = df["objects_present"].apply(
        lambda x: ";".join(x) if isinstance(x, list) else ""
    )

    df.to_excel(path, index=False, engine="openpyxl")
    print(f"✓ Saved: {path} ({len(df)} rows)")

def process_all_images(num_images: Optional[int] = None) -> List[Dict[str, Any]]:
    if num_images is None:
        num_images = len(image_files)

    target_files = image_files[:num_images]
    print(f"\n{'='*70}\nPROCESSING {len(target_files)} IMAGES — PREFIX={PREFIX}\n{'='*70}\n")

    rows, done_ids = load_existing_rows(OUTPUT_EXCEL)
    failed = []

    for idx, fname in enumerate(tqdm(target_files, desc="Processing", unit="img"), 1):
        image_id = fname.replace(".png", "")
        if image_id in done_ids:
            continue

        img_path = os.path.join(IMAGE_DIR, fname)
        print(f"\n[{idx}/{len(target_files)}] {fname}")

        g = call_gemini_api(img_path)
        if g is None:
            failed.append(fname)
            print("    ✗ Skipped")
            continue

        row = {
            "id": image_id,
            "image": fname,
            "page_type": g["page_type"],
            "has_text": g["has_text"],
            "has_table": g["has_table"],
            "objects_present": g["objects_present"],
            "caption_short": g["caption_short"],
            "caption_detail": g["caption_detail"],
            "text_in_image": g["text_in_image"],
            "review_priority": g["review_priority"],
            "auto_flags": g["auto_flags"],
            "notes": g["notes"],
            # QA columns
            "is_checked": 0,
            "error_tags": "",
            "change_log": "",
        }

        rows.append(row)
        done_ids.add(image_id)
        print("    ✓ Success")

        if SAVE_EVERY and (len(rows) % SAVE_EVERY == 0):
            save_rows_to_excel(rows, OUTPUT_EXCEL)

    # final save
    save_rows_to_excel(rows, OUTPUT_EXCEL)

    print(f"\n{'='*70}\nDONE\n{'='*70}")
    print(f"✓ Success rows: {len(rows)}")
    if failed:
        print(f"✗ Failed images: {len(failed)}")
        for f in failed[:20]:
            print(f"  - {f}")
        if len(failed) > 20:
            print("  ...")

    return rows

# %%
# ===== RUN =====
rows = process_all_images(num_images=None)

# %% [markdown]
# ## 7. THỐNG KÊ NHANH

# %%
df = rows_to_dataframe(rows)
df["auto_flags"] = df["auto_flags"].apply(lambda x: ";".join(x) if isinstance(x, list) else ("" if pd.isna(x) else str(x)))

print("\nSTATS")
print(f"- Total: {len(df)}")
print(f"- has_text=True: {(df['has_text']==True).sum()}")
print(f"- has_table=True: {(df['has_table']==True).sum()}")
print(f"- review_priority=high: {(df['review_priority']=='high').sum()}")
print(f"- avg len(caption_short): {df['caption_short'].astype(str).str.split().str.len().mean():.1f} words")
print(f"- avg len(caption_detail): {df['caption_detail'].astype(str).str.len().mean():.0f} chars")

# %% [markdown]
# ## 8. (Tuỳ chọn) Inspect 1 sample

# %%
import matplotlib.pyplot as plt

def inspect_sample(df: pd.DataFrame, index: int = 0) -> None:
    if df is None or df.empty:
        print("⚠ No data")
        return
    row = df.iloc[index]
    img_path = os.path.join(IMAGE_DIR, row["image"])
    img = Image.open(img_path).convert("RGB")

    plt.figure(figsize=(12, 8))
    plt.imshow(img)
    plt.title(f"{row['id']}", fontsize=14, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    print(f"\nID: {row['id']}")
    print(f"page_type: {row['page_type']} | has_text={row['has_text']} | has_table={row['has_table']} | review_priority={row['review_priority']}")
    print("\ncaption_short:\n", row["caption_short"])
    print("\ncaption_detail:\n", row["caption_detail"])
    print("\ntext_in_image:\n", row["text_in_image"])

inspect_sample(df, 0)


