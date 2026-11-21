# Dữ liệu Ứng dụng 1 (Chương 3) — Groceries

## groceries.csv

CSDL giỏ hàng thật của một cửa hàng bán lẻ, là bộ dữ liệu `Groceries` đi kèm gói R
[`arules`](https://cran.r-project.org/package=arules) (Hahsler, Grün, Hornik 2005; mô tả trong
Hahsler, Grün, Hornik, *arules — A Computational Environment for Mining Association Rules and
Frequent Item Sets*, JSS 2005).

- Nguồn tải: <https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/master/groceries.csv>
- Tải ngày: 21/11/2026
- Kích thước: 500.843 byte

### Định dạng

Mỗi dòng là **một giỏ hàng**, các món cách nhau bằng dấu phẩy, **không có dòng header**, item là
**tên tiếng Anh** (ví dụ `whole milk`) nên phải qua `src.utils.encode` trước khi chạy `fpgrowth`.

```
citrus fruit,semi-finished bread,margarine,ready soups
tropical fruit,yogurt,coffee
whole milk
```

### Thông số (kiểm tra lại được bằng lệnh dưới)

| | |
|---|---|
| Số giỏ | 9.835 |
| Số item phân biệt | 169 |
| Tổng lượt item | 43.367 |
| Độ dài giỏ trung bình | 4,4095 |
| Giỏ có item trùng | 0 |

```bash
python -c "rows=[l for l in open('data/app1/groceries.csv',encoding='utf-8') if l.strip()]; tx=[[x.strip() for x in r.split(',') if x.strip()] for r in rows]; print(len(tx), len({i for t in tx for i in t}), sum(len(t) for t in tx))"
```

### Vì sao chọn bộ này

1. Item có **tên đọc được**, nên mới diễn giải được ý nghĩa kinh doanh của luật kết hợp — yêu cầu
   của đề. `data/benchmark/retail.txt` tuy lớn hơn nhiều nhưng item đã ẩn danh thành số.
2. Kết quả của bộ này **đã được công bố rộng rãi**, nên nhóm có mốc để kiểm chứng cài đặt của mình:

   | Kiểm chứng | Giá trị |
   |---|---|
   | support(`whole milk`) | 2513 / 9835 = 0,25552 |
   | `{other vegetables, yogurt} -> {whole milk}` | sup 0,02227 · conf 0,51288 · lift 2,00723 |
   | `{butter} -> {whole milk}` | sup 0,02755 · conf 0,49725 · lift 1,94605 |
   | số luật tại minsup 0,01 và minconf 0,5 | 15 |

   Nhóm so **kết quả số** với các giá trị đã công bố này. Không đọc, không chạy, không dịch code của
   `arules` — toàn bộ phần khai thác tập phổ biến và sinh luật là cài đặt của nhóm.
3. Chỉ 500 KB nên đưa thẳng vào repo được, notebook trên Colab không phải tải mạng.
