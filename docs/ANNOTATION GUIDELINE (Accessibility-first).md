# ANNOTATION GUIDELINE (Accessibility-first)

<aside>
💡

**Dự án:** Vietnamese Image Captioning – SGK Tiểu học (Cánh Diều, lớp 1–3)

**Phiên bản:** v1.3 (cập nhật theo phản hồi giảng viên + mục tiêu hỗ trợ người khiếm thị)

**Ngày áp dụng:** 12/12/2025

</aside>

# 0) Quyết định dự án cố định

- **Không tách trang** (không split, không cắt ảnh).
- **Không suy luận “ý nghĩa giáo dục/đạo đức”** trong caption.
- Bắt buộc có **2 loại caption: `caption_short` và `caption_detail`**.
- **Độ chính xác** được kiểm tra **trên cả 2 loại caption**.

---

# 1) Mục tiêu dataset và vai trò của từng caption

## 1.1 Mục tiêu

Tạo dữ liệu captioning tiếng Việt cho ảnh trang SGK, có thể dùng để:

- Huấn luyện/finetune mô hình VLM (đặc biệt mô hình Instruct/Chat).
- Hỗ trợ người khiếm thị thông qua **caption_detail dạng thuyết minh theo luồng nghe**, trong đó chữ xuất hiện đến đâu được dẫn đến đó.

## 1.2 Vai trò theo giảng viên

- **`caption_detail` (mô tả chi tiết – phần “nêu kỹ”)**: áp dụng chặt các ràng buộc, mô tả đầy đủ bố cục và nội dung; phù hợp làm “thuyết minh” cho người khiếm thị.
- **`caption_short` (mô chung chung)**: 1–2 câu tổng quan, ít chi tiết; giúp mô hình học chế độ “brief” và phục vụ đánh giá ở mức tổng quát.

## 1.3 Nguyên tắc vàng (bắt buộc)

1. **Không suy luận giáo dục/đạo đức**: cấm các cụm như “bài học”, “giáo dục”, “đức tính”, “nhắc nhở”, “giúp học sinh…”, “nên/cần phải…”.
2. **Không bịa/hallucinate**: chỉ mô tả điều quan sát được. Nếu không chắc, nói “không rõ” hoặc “khó xác định”.
3. **Một trang = một ảnh**.
4. **Tính kiểm chứng**: câu trong `caption_short` phải phù hợp với nội dung có thể kiểm từ ảnh và/hoặc `caption_detail`.

---

# 2) Field dữ liệu và định nghĩa

## 2.1 Field làm việc (Excel) – khuyến nghị tối thiểu

| Field | Bắt buộc | Mục đích |
| --- | --- | --- |
| `id` | Có | định danh duy nhất |
| `image` | Có | tên file ảnh |
| `caption_short` | Có | mô chung chung (brief) |
| `caption_detail` | Có | thuyết minh chi tiết (accessibility-first) |
| `is_checked` | Có | 0/1 |
| `error_tags` | Có | taxonomy tag lỗi |
| `change_log` | Có | mô tả sửa đổi ngắn |

> Lưu ý: text_in_image vẫn hữu ích để kiểm nhanh OCR/đối soát, nhưng caption_detail không trình bày OCR thành một khối tách rời nữa.
> 

## 2.2 Định nghĩa chính

### A) `caption_short` (mô chung chung)

- **1–2 câu**, tiếng Việt, trung tính.
- Mô tả **loại trang + thành phần nổi bật** (tiêu đề, đoạn văn, tranh minh họa, bảng, bài tập…).
- **Không dán OCR dài**, không trích nhiều dòng chữ.

**Khuyến nghị độ dài:** 15–40 từ.

### B) `caption_detail` (chi tiết – thuyết minh theo luồng nghe)

- Là một đoạn thuyết minh mạch lạc, **đi từ tổng quan đến chi tiết**, theo thứ tự đọc **trên → dưới**, **trái → phải**.
- **Chữ trong ảnh được đọc “đến đâu dẫn đến đó”** (inline OCR).
- **Mọi đoạn chữ trích phải nguyên văn 100%** và đặt trong ngoặc kép “…”.

### C) Bảng biểu (nếu có)

- Trong `caption_detail`, mô tả cấu trúc bảng theo hướng nghe: vị trí bảng, số cột/hàng (ước lượng), tên cột/hàng (nếu có), rồi đọc nội dung theo thứ tự hợp lý (ví dụ: theo hàng).
- Khi đọc chữ trong ô, vẫn phải **nguyên văn** trong ngoặc kép.

---

# 3) Template `caption_detail`

**Cấu trúc bắt buộc (không cần tiêu đề cố định, nhưng phải đủ 3 lớp thông tin):**

## (1) Tổng quan trang (1–3 câu)

- Trang thuộc loại gì (bìa/mục lục/nội dung/bài tập), bố cục lớn gồm những phần nào (phần trên có gì, giữa có gì, dưới có gì).

## (2) Thuyết minh theo luồng đọc (nhiều câu)

- Mô tả từng khối nội dung theo thứ tự: **vị trí + loại khối + nội dung**.
- **Gặp chữ ở đâu đọc ngay ở đó**, dẫn dắt tự nhiên:
    - “Ở góc trên trái có nhãn ghi “…”.“
    - “Bên cạnh là dòng tiêu đề “…”.“
    - “Trong bong bóng thoại có dòng chữ: “…”.“

## (3) Kết thúc + ghi chú (1–2 câu)

- Nêu số trang nếu có (nguyên văn).
- Ghi chú phần mờ/khó đọc/không chắc.

**Quy tắc trích chữ**

- Chỉ trích chữ khi: (a) là tiêu đề/nhãn/đề bài/bong bóng thoại/nội dung bảng/số trang… và (b) nhìn rõ.
- Nếu chữ dài: có thể trích theo từng dòng/khối, nhưng vẫn phải có dẫn dắt “đoạn văn ghi…”.

---

# 4) Quy chuẩn nội dung theo loại trang (để thống nhất)

- **cover (bìa):** mô tả tiêu đề sách, lớp, bộ sách, hình minh họa bìa, thông tin NXB (nếu có).
- **toc (mục lục):** mô tả danh sách mục/bài và số trang.
- **content (nội dung):** mô tả tiêu đề bài/mục, đoạn văn, tranh minh họa, hoạt động/hướng dẫn.
- **exercise (bài tập):** mô tả dạng câu hỏi/đề bài, khung bài tập, chỗ trống (nếu có).
- **blank (trang trắng):** nói rõ gần như không có nội dung.

---

# 5) Ví dụ đúng/sai (chuẩn hóa để giảm cảm tính)

## 5.1 Sai do suy luận giáo dục (cấm)

- **Sai:** “Bức tranh dạy học sinh biết lễ phép.”
- **Đúng:** “Trang có mục hoạt động và tranh minh họa cảnh một học sinh chào người lớn, kèm các dòng hướng dẫn.”

## 5.2 Sai do OCR tách rời, khó nghe (không phù hợp accessibility)

- **Sai:** “Văn bản trong ảnh: … (dán một khối dài không dẫn dắt)”
- **Đúng:** “Ngay dưới nhãn ‘KHÁM PHÁ’ là dòng tiêu đề ‘…’. Trong hình tròn số 1, bong bóng thoại ghi ‘…’.”

## 5.3 Sai do hallucination (bịa)

- **Sai:** “Bé mặc áo đỏ” (khi màu không chắc).
- **Đúng:** “Bé mặc áo màu sáng (màu không rõ).”

## 5.4 Trang có bảng (đúng cách đọc cho người nghe)

- **Đúng:** “Ở nửa dưới trang có một bảng. Hàng tiêu đề có các cột ‘…’. Dòng đầu tiên ghi ‘…’ …”

## 5.5 Khi trang yêu cầu đếm số lượng hoặc đọc đồng hồ:

- **Không bắt buộc phải nêu con số chính xác** trong `caption_detail` nếu không chắc.
- Ưu tiên mô tả **cấu trúc** thay vì **kết quả**.
- Ví dụ đúng (Counting):
    - **Sai** (ép đếm): “Có 100 củ cà rốt được chia thành 10 bó.”
    - **Đúng** (an toàn): “Có nhiều bó cà rốt, mỗi bó gồm các củ được buộc lại; trang yêu cầu học sinh đếm số lượng.” hoặc: “Trang minh họa các bó cà rốt giống nhau, bên cạnh là yêu cầu đếm số củ.”
- Ví dụ đúng (Clock)
    - **Sai** (ép đọc giờ): “Kim giờ chỉ số 4, kim phút chỉ số 6.”
    - **Đúng** (an toàn): “Trang có hình một chiếc đồng hồ kim, với kim giờ và kim phút được vẽ rõ để học sinh quan sát và xác định thời gian.”
- Nếu Gemini **đã đọc giờ** → giữ nguyên + gắn tag nếu sai.

---

# 6) Checklist kiểm tra (Pass/Fail) – tách riêng short và detail

## 6.1 Checklist chung

- [ ]  Không có suy luận đạo đức/giáo dục.
- [ ]  Không bịa chi tiết không thấy.
- [ ]  Mô tả theo thứ tự hợp lý, không nhảy ý gây khó nghe.

## 6.2 Checklist cho `caption_short`

- [ ]  1–2 câu, mô chung chung đúng loại trang và thành phần chính.
- [ ]  Không dán OCR dài, không liệt kê quá chi tiết.

## 6.3 Checklist cho `caption_detail` (accessibility-first)

- [ ]  Có **tổng quan trang** trước khi đi chi tiết.
- [ ]  Chữ trong ảnh được **dẫn vào đúng ngữ cảnh**, trích trong ngoặc kép và **nguyên văn**.
- [ ]  Thuyết minh theo luồng đọc (trên→dưới, trái→phải), người nghe định vị được chữ thuộc phần nào.

---

# 7) Error Taxonomy (tag lỗi)

## 7.1 Nhóm OCR

- `OCR_MISSING` – thiếu chữ đáng kể so với ảnh
- `OCR_WRONG` – sai ký tự/nhầm chữ
- `OCR_UNREADABLE` – chữ mờ nhưng không đánh dấu `[mờ]/[không đọc được]`
- `OCR_NOT_CONTEXTUALIZED` – caption_detail đọc chữ nhưng **không dẫn ngữ cảnh** (người nghe không biết chữ thuộc phần nào)

## 7.2 Nhóm Caption

- `HALLUCINATION` – bịa chi tiết
- `WRONG_LAYOUT` – mô tả bố cục/vị trí sai rõ ràng
- `SUBJECTIVE_REASONING` – dính suy luận giáo dục/đạo đức
- `TOO_LONG_SHORT` – caption_short quá dài / liệt kê vụn vặt
- `DETAIL_INCOHERENT_FLOW` – caption_detail nhảy ý, khó nghe, không theo luồng đọc
- `MISQUOTED_TEXT` – trích chữ không nguyên văn/thiếu dấu/khác ảnh

## 7.3 Nhóm Math Perception

- `COUNTING_WRONG` - Gemini **đếm sai số lượng rõ ràng** (ví dụ ảnh có 10 bó × 10 củ nhưng mô tả là 90 hoặc 11 bó)
- `CLOCK_READING_WRONG`- Gemini **đọc sai kim giờ/kim phút** (ví dụ 3:30 nhưng ghi 4:30)

👉 **Quan trọng**:

- Không sửa số đếm trong caption_detail nếu model không chắc
- Không “chỉnh cho đúng” bằng suy luận của annotator
    
    → Chỉ **đánh tag + ghi chú**
    

## 7.4 Nhóm Kỹ thuật

- `ID_ISSUE` – trùng hoặc sai format
- `IMAGE_MISMATCH` – sai tên ảnh

## 7.5 Format ghi log

- `error_tags`: `TAG1, TAG2, ...`
- `change_log` (1 dòng): `Fix: <đã sửa gì> | Reason: <TAG chính>`

---

# 8) Quy trình QA & Adjudication (phù hợp tiến độ 1 tuần)

## 8.1 Quy tắc adjudication (ra quyết định nhanh)

- Nếu câu có nguy cơ suy luận → **xóa hoặc viết lại trung tính**.
- Nếu OCR không chắc → dùng `[không đọc được]`, không đoán.
- Nếu `caption_short` và `caption_detail` mâu thuẫn → sửa `caption_short` cho khớp ảnh và thuyết minh trong detail.
- Nếu caption_detail đọc chữ mà không dẫn ngữ cảnh → gắn `OCR_NOT_CONTEXTUALIZED` và chỉnh theo template v1.2.

## 8.2 Tiêu chí “>90% accuracy” (áp dụng cho cả 2)

- `caption_short`: đúng tổng quan (loại trang + thành phần chính), không sai lớn.
- `caption_detail`: đúng bố cục, đúng chuỗi chữ khi trích, luồng nghe rõ ràng.

---

# 9) Phụ lục – Chuẩn hóa prompt cho finetune VLM Instruct (khuyến nghị)

Vì giảng viên nói nên “kết hợp cả 2”, nhóm có thể tạo 2 instruction cố định:

## 9.1 Prompt cho `caption_short` (Brief)

“Hãy mô tả ngắn gọn (1–2 câu) nội dung trang SGK trong ảnh. Chỉ mô tả những gì nhìn thấy, không suy luận.”

## 9.2 Prompt cho `caption_detail` (Detailed, Accessibility-first)

“Hãy thuyết minh chi tiết trang SGK trong ảnh theo luồng đọc trên xuống dưới. Khi gặp chữ trong ảnh, hãy dẫn vào đúng ngữ cảnh và trích nguyên văn trong ngoặc kép. Không suy luận.”

---

# 10) Mẫu `caption_detail` đúng kiểu (rút gọn)

“Ở phần trên trang có mục … với dòng chữ ‘…’. Bên dưới là nhãn ‘…’ và tiêu đề ‘…’. Ở trung tâm có dòng chữ lớn ‘…’, xung quanh là … hình minh họa. Trong hình số 1…, bong bóng thoại ghi ‘…’ … Cuối trang có ‘…’ và số trang ‘…’. Ghi chú: …”

---