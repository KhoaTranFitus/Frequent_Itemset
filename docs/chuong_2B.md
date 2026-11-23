# Chương 2, nửa B: Bộ nhớ, độ dài giao dịch, so sánh với SPMF, hướng tối ưu

Người phụ trách: **Khoa**. Số liệu lấy từ `data/output/exp/` (sinh bằng các script trong `scripts/`), biểu đồ trong `docs/figures/`.
File này viết theo văn phong báo cáo, chép sang mẫu IEEE được; chỗ ghi "Hình ?" và "Bảng ?" thì đánh số lại theo báo cáo chung.

---

## 0. Khái niệm dùng trong phần này

- **Peak memory (bộ nhớ đỉnh):** lượng RAM lớn nhất mà chương trình chiếm **tại một thời điểm** trong suốt lúc chạy. Không phải tổng, cũng không phải trung bình. Đây là con số quyết định máy có đủ RAM để chạy thuật toán hay không.
- **`tracemalloc`:** module có sẵn của Python, theo dõi bộ nhớ do Python cấp phát. `tracemalloc.get_traced_memory()` trả về cặp (bộ nhớ hiện tại, bộ nhớ đỉnh), tính bằng byte.
- **Thực nghiệm có kiểm soát (controlled experiment):** thay đổi **đúng một yếu tố**, giữ nguyên mọi yếu tố khác, để chắc chắn rằng kết quả thay đổi là do yếu tố đó.
- **Phân bố Zipf:** item thứ k có xác suất xuất hiện tỉ lệ với 1/k: item 1 phổ biến nhất, item 2 bằng một nửa, item 3 bằng một phần ba… Mô phỏng dữ liệu thật, nơi vài mặt hàng được mua rất nhiều còn phần lớn mặt hàng hiếm.
- **Phân bố Poisson:** sinh số nguyên ngẫu nhiên có trung bình cho trước; dùng để độ dài giao dịch dao động tự nhiên quanh một giá trị L.

---

## 1. Sử dụng bộ nhớ: bản cơ bản và bản tối ưu

### Thiết lập

- Script: `scripts/exp_memory.py` → `data/output/exp/memory.csv` → Hình ? (`docs/figures/memory.png`).
- Đo peak memory bằng `tracemalloc` cho hai bản cài đặt: **bản cơ bản** (`fpgrowth_basic.py`) và **bản tối ưu** (`fpgrowth.py`, thêm xử lý single path theo Lemma 3.2).
- Mỗi CSDL đo tại **minsup giữa** (mức thứ 4 trong danh sách 7 mức của `src/config.py`).
- Chỉ đo **phần thuật toán**: dữ liệu được đọc vào bộ nhớ **trước** khi bắt đầu đo, khớp với cách đo thời gian ở nửa A.
- Mỗi bản đo **một lần**: chạy lại hai lần cho kết quả lệch nhau không quá 0,01 MB, vì cùng dữ liệu thì cùng số node và cùng cấu trúc. Thời gian thì dao động theo tải của máy nên mới cần lấy trung vị 3 lần; bộ nhớ thì không.
- Đo bộ nhớ chạy **riêng** với đo thời gian, vì `tracemalloc` làm chương trình chậm đi đáng kể.

### Kết quả

**Bảng ?.** Peak memory tại minsup giữa.

| CSDL | Loại | minsup | Bản cơ bản (MB) | Bản tối ưu (MB) | Thay đổi |
|---|---|---|---|---|---|
| Chess | dày | 0,75 | 4,20 | 3,15 | **−25,0%** |
| Mushroom | dày | 0,2 | 10,66 | 8,37 | **−21,5%** |
| Retail | thưa | 0,004 | 39,91 | 39,82 | −0,2% |
| T10I4D100K | thưa | 0,004 | 204,63 | 204,66 | +0,01% |

### Nhận xét

1. **Tối ưu single path giảm bộ nhớ 21–25% trên dữ liệu dày, gần như không đổi trên dữ liệu thưa.**
2. **Vì sao.** Peak memory gần bằng *FP-tree gốc* cộng với *các conditional FP-tree đang mở trên đường đệ quy*. Cây gốc thì hai bản dựng **giống hệt nhau** (cùng Algorithm 1 của bài báo). Hai bản chỉ khác nhau khi gặp một cây chỉ có một nhánh: bản tối ưu sinh luôn mọi tổ hợp của nhánh đó (Lemma 3.2) mà **không dựng thêm conditional tree nào**, còn bản cơ bản vẫn đệ quy và dựng từng cây con. Vậy bản tối ưu chỉ tiết kiệm được phần conditional tree.
3. **Dữ liệu dày** (Chess, Mushroom): giao dịch dài, chung nhiều tiền tố, nên khi đệ quy xuống sâu, các conditional tree rất hay co lại thành một nhánh. Bản tối ưu cắt được nhiều cây con, nên đỉnh bộ nhớ giảm rõ.
4. **Dữ liệu thưa** (Retail, T10I4D100K): rất nhiều item, giao dịch ít chung tiền tố, nên cây gốc **rậm và lớn**, còn các conditional tree thì rất nhỏ so với nó. Bài báo cũng ghi nhận điều này: khi support thấp, FP-tree trở nên "bushy" và mức chia sẻ tiền tố giảm (mục 5.3). Đỉnh bộ nhớ gần như chỉ là cây gốc, mà cây gốc thì hai bản như nhau. Mức chênh +0,03 MB ở T10I4D100K là nhỏ hơn 0,02%, coi như bằng nhau.
5. **Hệ quả:** muốn giảm bộ nhớ trên dữ liệu thưa thì phải **làm nhỏ chính cây gốc**, không phải cắt bớt cây con. Đây là cơ sở cho hướng tối ưu 1 và 2 ở mục 4.

---

## 2. Ảnh hưởng của độ dài giao dịch trung bình

### Thiết lập

- Script: `scripts/exp_txlen.py` → `data/output/exp/txlen.csv` → Hình ? (`docs/figures/txlen.png`).
- Đây là **thực nghiệm có kiểm soát** trên CSDL tổng hợp, vì các CSDL thật khác nhau ở quá nhiều yếu tố cùng lúc (số item, số giao dịch, phân bố item) nên không tách riêng được ảnh hưởng của độ dài.
- **Giữ cố định:** 10.000 giao dịch, 200 item, minsup 0,05, seed 42. **Chỉ thay đổi:** độ dài trung bình L = 5, 10, 15, 20, 25, 30.
- Độ dài từng giao dịch lấy theo **phân bố Poisson** với trung bình L; mỗi giao dịch chọn item **không lặp** theo **phân bố Zipf** (item thứ k có xác suất tỉ lệ 1/k).
- **Vì sao không chọn item đều nhau:** nếu đều, với L = 30 mỗi item chỉ xuất hiện trong khoảng 15% giao dịch, một cặp item xuất hiện chung khoảng 0,15 × 0,15 ≈ 2%, dưới minsup 5%, nên gần như chỉ có tập 1 item và thực nghiệm không cho thấy gì.
- CSV ghi **độ dài trung bình thực tế** của dữ liệu sinh ra (Poisson chỉ cho trung bình xấp xỉ L). Thời gian là trung vị 3 lần chạy, bản tối ưu.

### Kết quả

**Bảng ?.** Thời gian chạy và số itemset theo độ dài giao dịch trung bình.

| Độ dài TB | Số itemset | Thời gian (s) |
|---|---|---|
| 5,03 | 37 | 0,039 |
| 10,00 | 251 | 0,110 |
| 14,94 | 1.357 | 0,375 |
| 20,00 | 6.794 | 0,871 |
| 24,96 | 31.769 | 2,424 |
| 29,95 | 145.142 | 7,078 |

### Nhận xét

1. **Thuật toán bị ảnh hưởng mạnh bởi độ dài giao dịch.** Độ dài tăng 6 lần (5 → 30) nhưng thời gian tăng khoảng **180 lần**, số itemset tăng khoảng **3.900 lần**. Đường thời gian cong lên rõ rệt, tức tăng **phi tuyến**; đường số itemset gần như thẳng trên trục log, tức tăng **theo hàm mũ**.
2. **Giải thích theo bài báo.** Lemma 2.2: chiều cao FP-tree bị chặn bởi số item phổ biến lớn nhất trong một giao dịch. Giao dịch dài hơn thì cây sâu hơn, conditional pattern base dài hơn và đệ quy sâu hơn. Đồng thời, giao dịch dài chứa nhiều item phổ biến cùng lúc hơn; một tập phổ biến k item kéo theo 2^k − 1 tập con cũng phổ biến, nên số tổ hợp bùng nổ.
3. **Thời gian tăng chậm hơn số itemset** nhờ Lemma 3.2: gặp nhánh đơn thì sinh cả loạt tổ hợp cùng lúc mà không dựng thêm cây. Phần lớn chi phí nằm ở dựng cây và đệ quy, còn số tập sinh ra thì nhiều hơn số cây phải dựng rất nhiều.
4. **Liên hệ với CSDL thật:** điều này giải thích vì sao Chess (giao dịch dài 37 item) chỉ chạy được ở minsup rất cao (0,6–0,9), còn Retail và T10I4D100K (giao dịch dài khoảng 10) chạy được ở minsup rất thấp (0,001).

---

## 3. So sánh với SPMF: điểm mạnh và điểm yếu

### Thiết lập

- Số liệu từ `data/output/exp/runtime.csv` (script `exp_runtime.py` của nửa A), 4 CSDL × 7 mức minsup = 28 ca.
- Thời gian SPMF lấy từ dòng `Total time` do SPMF tự in ra; thời gian của nhóm chỉ tính phần thuật toán, không tính đọc file.

**Bảng ?.** Tỉ lệ thời gian bản tối ưu / SPMF (lớn hơn 1 là nhóm chậm hơn).

| CSDL | minsup cao nhất | minsup thấp nhất | Khoảng tỉ lệ |
|---|---|---|---|
| Chess | 0,47 (0,9) | 3,07 (0,6) | 0,5 → 3,1 |
| Mushroom | 0,69 (0,5) | 8,91 (0,05) | 0,6 → 8,9 |
| Retail | 1,44 (0,01) | 3,84 (0,001) | 1,4 → 3,8 |
| T10I4D100K | 4,33 (0,01) | 5,29 (0,001) | 4,3 → 5,3 |

### Điểm mạnh

1. **Đúng 100%.** Cả 28 ca khớp hoàn toàn với SPMF: cùng tập phổ biến và cùng support (cột `match_pct`).
2. **Cùng hành vi với SPMF.** Đường thời gian của nhóm tăng **cùng hình dạng** với SPMF khi minsup giảm, trên cả 4 CSDL. Điều này cho thấy nhóm cài đúng thuật toán; chênh lệch còn lại là một hệ số do ngôn ngữ và cách cài đặt, không phải do sai thuật toán.
3. **Tối ưu single path có hiệu quả thật trên dữ liệu dày:** bản tối ưu nhanh hơn bản cơ bản tới 3,5 lần (Mushroom, minsup 0,1) và giảm 21–25% bộ nhớ (mục 1).
4. Ở minsup cao trên dữ liệu dày (Chess 0,9–0,8, Mushroom 0,5–0,3), thời gian của nhóm còn **thấp hơn** SPMF. Tuy vậy, xem lưu ý 2 bên dưới: kết quả này chủ yếu do cách đo khác nhau, không nên coi là nhóm nhanh hơn SPMF.

### Điểm yếu

1. **Chậm hơn SPMF ở minsup thấp:** khoảng 3–4 lần trên Chess và Retail, khoảng 5 lần trên T10I4D100K, tới gần 9 lần trên Mushroom 0,05 (4,1 triệu tập phổ biến). Nguyên nhân chính:
   - Python là ngôn ngữ thông dịch, còn Java được biên dịch JIT (dịch sang mã máy lúc chạy).
   - Mỗi node FP-tree là một object Python có `dict` con: tốn nhiều bộ nhớ, truy cập chậm, và tạo hàng triệu object làm bộ thu gom rác (garbage collector) phải làm việc nhiều.
   - Với Mushroom 0,05, phần lớn thời gian là sinh và lưu 4,1 triệu tuple vào `dict` kết quả; đây là chi phí mà Python chịu nặng nhất.
2. **Tối ưu hiện tại gần như vô dụng trên dữ liệu thưa:** trên Retail và T10I4D100K, bản tối ưu và bản cơ bản chênh nhau trong khoảng ±5%, ngang mức dao động của phép đo, cả về thời gian lẫn bộ nhớ.

### Lưu ý khi đọc số liệu

1. **Phép đo có dao động.** Thực nghiệm đã được chạy đầy đủ hai lần (`runtime.csv` giữ lần sau); giữa hai lần, thời gian bản tối ưu của cùng một ca lệch nhau từ −38% đến +43% (ví dụ Mushroom 0,05: 8,6 s và 12,3 s). Vì vậy chỉ nên so sánh **xu hướng** và **chênh lệch lớn** (gấp đôi trở lên); chênh lệch dưới khoảng 20% không đủ để kết luận.
2. **Hai bên không đo cùng một thứ.** Thời gian SPMF là `Total time` do SPMF tự báo, đo trong một JVM mới khởi động nên chưa được JIT tối ưu, và có thể gồm cả đọc file, ghi kết quả. Thời gian của nhóm chỉ tính phần thuật toán. Ở các ca nhỏ (dưới khoảng 0,1 s), chênh lệch cách đo này lấn át chênh lệch thật, nên tỉ lệ dưới 1 ở minsup cao không có nghĩa là nhóm nhanh hơn.

---

## 4. Hướng tối ưu tiếp theo

Mỗi hướng gồm: vấn đề quan sát được, giải pháp, và lý do kỳ vọng hiệu quả.

### Hướng 1: Lưu FP-tree bằng mảng số nguyên thay cho object

- **Vấn đề:** trên dữ liệu thưa, peak memory gần như toàn bộ là cây gốc (mục 1), và mỗi node là một object Python có `dict` con, tốn hàng trăm byte cho một node chỉ mang vài số nguyên.
- **Giải pháp:** lưu các node bằng nhiều mảng song song: `item[i]`, `count[i]`, `parent[i]`, `next_link[i]` (node-link), dùng `array` của Python hoặc mảng numpy. Con được tìm qua một bảng băm duy nhất `(parent, item) → i`, thay cho một `dict` riêng ở mỗi node.
- **Kỳ vọng:** bộ nhớ mỗi node giảm từ hàng trăm byte xuống vài chục byte; số object Python giảm từ hàng triệu xuống vài cái, nên bộ thu gom rác nhẹ hẳn. Đây là hướng duy nhất trong danh sách tác động trực tiếp vào cây gốc, đúng chỗ tối ưu hiện tại không chạm tới.

### Hướng 2: Projected database cho dữ liệu thưa (mục 4 của bài báo)

- **Vấn đề:** bài báo chỉ ra rằng khi support thấp, FP-tree trở nên rậm, ít chia sẻ tiền tố, và chi phí con trỏ có thể làm cây lớn hơn cả dữ liệu gốc (mục 5.3, Hình 8–9 của bài báo). Đây đúng là tình huống của Retail và T10I4D100K.
- **Giải pháp:** thay vì dựng ngay FP-tree, chiếu CSDL thành các *projected database* theo từng item (partition projection), và chỉ dựng FP-tree khi một projected database đủ dày. Các tác giả dùng ngưỡng mật độ 3% trong thực nghiệm của họ.
- **Kỳ vọng:** giảm cả bộ nhớ lẫn thời gian trên đúng hai CSDL thưa mà tối ưu single path không có tác dụng. Projected database cũng cho phép chạy khi FP-tree không vừa bộ nhớ.

### Hướng 3: Mảng đếm cặp kiểu FP-growth* (Grahne & Zhu, 2003)

- **Vấn đề:** mỗi lần dựng conditional FP-tree, cài đặt hiện tại phải duyệt các prefix path **hai lần**: một lần đếm support từng item, một lần chèn vào cây mới.
- **Giải pháp:** trong lúc dựng một cây, đếm luôn tần suất xuất hiện chung của từng cặp item vào một mảng. Khi dựng conditional tree cho item x, lấy support của các item đi cùng x từ mảng này, bỏ được lượt duyệt đếm.
- **Kỳ vọng:** giảm khoảng một nửa số lượt duyệt prefix path ở mỗi tầng đệ quy; hiệu quả nhất ở dữ liệu thưa, nơi có nhiều conditional tree nhỏ.

### Hướng tham khảo thêm

Phần kết luận của bài báo nhắc tới **H-mine**, thuật toán theo cùng triết lý pattern growth nhưng không dựng lại conditional FP-tree nhiều lần, và được báo cáo là nhanh hơn FP-Growth trên dữ liệu thưa. Một hướng xa hơn là chọn chiến lược theo mật độ dữ liệu: dữ liệu dày dùng FP-tree, dữ liệu thưa dùng H-struct hoặc projected database.

---

## 5. Tóm tắt cho notebook (ô nhận xét 2B)

```markdown
### Nhận xét (nửa B)
- Tối ưu single path giảm 21–25% bộ nhớ đỉnh trên dữ liệu dày (Chess, Mushroom), gần 0% trên dữ liệu thưa:
  đỉnh bộ nhớ chủ yếu là FP-tree gốc, mà tối ưu chỉ bớt được các conditional tree.
- Độ dài giao dịch tăng 6 lần làm thời gian tăng khoảng 180 lần và số itemset tăng khoảng 3.900 lần (phi tuyến),
  phù hợp với Lemma 2.2: giao dịch dài thì cây sâu và số tổ hợp bùng nổ.
- Khớp SPMF 100% trên cả 28 ca; chậm hơn SPMF khoảng 3–5 lần ở minsup thấp (tới 9 lần với Mushroom 0,05)
  do Python và cấu trúc node dạng object.
- Hướng tối ưu: FP-tree dạng mảng số nguyên; projected database cho dữ liệu thưa; mảng đếm cặp kiểu FP-growth*.
```

---

## Tài liệu tham khảo cho phần này

1. J. Han, J. Pei, Y. Yin, R. Mao. Mining Frequent Patterns without Candidate Generation: A Frequent-Pattern Tree Approach. *Data Mining and Knowledge Discovery*, 8, 53–87, 2004. (Lemma 2.2, Lemma 3.2, mục 4, mục 5.3, phần kết luận về H-mine.)
2. G. Grahne, J. Zhu. Efficiently Using Prefix-trees in Mining Frequent Itemsets. *Proc. IEEE ICDM Workshop on Frequent Itemset Mining Implementations (FIMI'03)*, 2003.
3. J. Pei, J. Han, H. Lu, S. Nishio, S. Tang, D. Yang. H-Mine: Hyper-Structure Mining of Frequent Patterns in Large Databases. *Proc. IEEE ICDM*, 2001.
4. P. Fournier-Viger et al. SPMF: An Open-Source Data Mining Library. https://www.philippe-fournier-viger.com/spmf/
