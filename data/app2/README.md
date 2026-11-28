# Dữ liệu Ứng dụng 2 — Splice-junction Gene Sequences

Bộ dữ liệu *Molecular Biology (Splice-junction Gene Sequences)* của UCI Machine Learning
Repository (Towell, Noordewier, Shavlik, 1992).

- Nguồn: <https://archive.ics.uci.edu/dataset/69/molecular+biology+splice+junction+gene+sequences>
- 3.190 chuỗi DNA của linh trưởng, mỗi chuỗi dài 60 nucleotide, ranh giới (nếu có) nằm chính giữa.

## Các file

| File | Nội dung |
|---|---|
| `splice.data` | dữ liệu: mỗi dòng gồm nhãn, tên mẫu, chuỗi 60 nucleotide, cách nhau bằng dấu phẩy |
| `splice.names` | mô tả gốc của UCI |
| `splice.data.Z` | bản nén của `splice.data` (đi kèm bộ tải gốc, nhóm không dùng) |
| `splice.theory`, `Index` | lý thuyết miền và danh mục file của UCI (nhóm không dùng) |
| `code.json` | bảng mã item → số do nhóm sinh, dùng chung cho cả ba nhãn |

## Nhãn

| Nhãn | Ý nghĩa | Số mẫu |
|---|---|---|
| `EI` | ranh giới exon → intron (**donor**) | 767 |
| `IE` | ranh giới intron → exon (**acceptor**) | 768 |
| `N` | không chứa ranh giới (đối chứng) | 1.655 |

> **Lưu ý:** `splice.names` gọi `IE` là "donors" và `EI` là "acceptors", ngược với quy ước sinh
> học. Trang UCI hiện tại và báo cáo của nhóm dùng quy ước đúng: **EI = donor, IE = acceptor**.

## Tiền xử lý

- Mỗi chuỗi là một giao dịch; item có dạng `P<vị trí>=<nucleotide>`, vị trí từ −30 đến +30 so với
  ranh giới (không có vị trí 0), ví dụ `P+1=G`.
- 15 chuỗi có ký tự không chắc chắn (`N`, `D`, `R`, `S` theo mã IUPAC); các ký tự này được bỏ qua
  thay vì đoán.
- Code đọc và biến đổi dữ liệu nằm trong `src/app2_bio.py`.
