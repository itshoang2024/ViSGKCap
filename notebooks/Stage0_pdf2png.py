# %% [markdown]
# # STAGE 0: CONVERT PDF TO PNG
# Chuyển file PDF ngữ liệu thô thành dạng ảnh với tên đặt theo cấu trúc sau: `SGK_<Tên bộ sách>_<Tên sách>_<Lớp>_<Tap?>_<Trang>` (nếu không có tập thì bỏ Tap). Ví dụ: `SGK_CanhDieu_DaoDuc_1_page_001`

# %%
# Install poppler
# !apt-get install -y poppler-utils # using on Colab
%conda install -q -c conda-forge poppler # using on conda (Windows)
%pip install -q pdf2image tqdm

# %%
from pathlib import Path

RAW_DIR = Path("../data/raw")
PROCESSED_DIR = Path("../data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# %%
import os
from pdf2image import convert_from_path
from tqdm import tqdm

prefix_map = {
    # Môn Đạo đức
    "dao-duc-1.pdf": "SGK_CanhDieu_DaoDuc_1",
    "dao-duc-2.pdf": "SGK_CanhDieu_DaoDuc_2",
    "dao-duc-3.pdf": "SGK_CanhDieu_DaoDuc_3",

    # Môn Tiếng Việt
    "tieng-viet-2-tap-mot.pdf": "SGK_CanhDieu_TiengViet_2_Tap1",
    "tieng-viet-2-tap-hai.pdf": "SGK_CanhDieu_TiengViet_2_Tap2",

    # Môn Toán
    "toan-1.pdf": "SGK_CanhDieu_Toan_1",
    "toan-3-tap-mot.pdf": "SGK_CanhDieu_Toan_3_Tap1",

    # Môn Tự nhiên và Xã hội
    "tu-nhien-va-xa-hoi-1.pdf": "SGK_CanhDieu_TuNhienVaXaHoi_1",
    "tu-nhien-va-xa-hoi-2.pdf": "SGK_CanhDieu_TuNhienVaXaHoi_2",
    "tu-nhien-va-xa-hoi-3.pdf": "SGK_CanhDieu_TuNhienVaXaHoi_3",
}

for pdf_name, prefix in prefix_map.items():
    print(f"\nĐang xử lý file: {pdf_name} …")

    pdf_path = os.path.join(RAW_DIR, pdf_name)
    pages = convert_from_path(pdf_path, dpi=200)

    for i, page in enumerate(tqdm(pages, desc=f"Đang convert {pdf_name}", unit="page"), start=1):
        fname = f"{prefix}_page_{str(i).zfill(3)}.png"
        out_path = os.path.join(PROCESSED_DIR, fname)
        page.save(out_path, "PNG")

print("\nDone!")


