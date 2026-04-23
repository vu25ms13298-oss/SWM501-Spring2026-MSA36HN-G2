# 🚗 Smart Driving Booking - Demo Flow Guide

> Hướng dẫn thực hiện demo toàn hệ thống - cho Học viên, Giáo viên, Admin

---

## 📋 Tài khoản Demo

### 👨‍🎓 Học Viên (Learners)
| Email | Password | Trình độ | Tín chỉ | Mục đích |
|-------|----------|---------|--------|---------|
| learner1@sds.vn | learner123 | Sơ cấp | 10 | Demo đặt lịch, hủy lịch |
| learner2@sds.vn | learner123 | Sơ cấp | 8 | Demo so sánh matching score |
| learner3@sds.vn | learner123 | Trung cấp | 12 | Demo lịch học tương tự |

### 👨‍🏫 Giáo Viên (Instructors)
| Email | Password | Tên | Mục đích |
|-------|----------|-----|---------|
| instructor1@sds.vn | instructor123 | Nguyễn Văn An | Demo xem lịch dạy, smart grouping |
| instructor2@sds.vn | instructor123 | Trần Thị Bích | Demo học viên cùng level |
| instructor3@sds.vn | instructor123 | Lê Văn Cường | Demo quản lý lịch |

### 👨‍💼 Admin
| Email | Password |
|-------|----------|
| admin@sds.vn | admin123 |

---

## 🎬 Demo Scenario: Luồng Đặt Lịch Thông Minh (15 phút)

### **Phase 1: Học Viên Đặt Lịch (5 phút)**

#### Bước 1: Đăng nhập Học viên
1. Truy cập: http://localhost:5173
2. Đăng nhập: `learner1@sds.vn` / `learner123`
3. **Kỳ vọng**: Thấy Dashboard với 10 tín chỉ, 0 buổi sắp tới

```
✨ Smart Booking: 
Hệ thống tự động ghép học viên cùng trình độ, 
đánh giá điểm phù hợp (0-100%), đề xuất ca học tối ưu.
```

#### Bước 2: Xem Danh Sách Ca Học
1. Click "📅 Đặt lịch học"
2. **Mặc định**: Ngày mai + 2 ngày
3. Click "Tìm kiếm" 
4. **Kỳ vọng**: Xem 6-10 ca học tuần tới với:
   - ⏰ Giờ học (8:00, 10:00, 14:00)
   - 👨‍🏫 Giáo viên tên
   - 🚗 Xe (Số sàn / Số tự động)
   - **Điểm phù hợp** (best_match_score): 
     - 🟢 **Phù hợp cao** (70-100%): Cùng trình độ Sơ cấp
     - 🟡 **Phù hợp vừa** (40-70%): Hỗn hợp trình độ
     - 🔴 **Phù hợp thấp** (<40%): Khác trình độ

#### Bước 3: So Sánh Matching Scores
1. **Chọn ca học với điểm phù hợp cao**
2. Click "Đặt lịch"
3. Xem modal xác nhận:
   ```
   Xác nhận đặt lịch
   🕐 Thời gian: 08:00 thứ 2, 28/04/2026
   👨‍🏫 Giáo viên: Nguyễn Văn An
   🚗 Xe: 51A-12345 (Số sàn)
   ⚠️ Sẽ trừ 1 tín chỉ
   ```
4. Click "Xác nhận"
5. **Kỳ vọng**: Thông báo "Đặt lịch thành công! Tín chỉ đã được trừ."

#### Bước 4: Kiểm Tra Lịch Của Tôi
1. Click "📋 Lịch học của tôi"
2. **Kỳ vọng**: Thấy buổi học vừa đặt trong danh sách confirmed

---

### **Phase 2: Giáo Viên Xem Lịch Dạy (5 phút)**

#### Bước 1: Đăng nhập Giáo viên
1. **Logout** khỏi tài khoản học viên (click avatar → Logout)
2. Đăng nhập: `instructor1@sds.vn` / `instructor123`
3. **Kỳ vọng**: Trang Lịch dạy

```
✨ Smart Grouping:
Hệ thống tự động ghép học viên cùng trình độ vào lớp của bạn.
```

#### Bước 2: Xem Lịch Dạy Theo Tuần
1. Chọn "Tuần" bằng input week picker (màn hình có chữ "Tuần:")
2. **Browser sẽ hiện**: ISO week format (VD: `2026-W18`)
3. **Hệ thống convert**: `2026-W18` → `2026-18` (fix bug)
4. **Kỳ vọng**: Xem 6-8 ca dạy trong tuần

Mỗi ca học hiển thị:
- ⏰ **Giờ**: 08:00 – 10:00
- 📅 **Ngày**: Thứ 2, 28/04
- 👥 **Học viên**: 1/3 (1 học viên, 3 chỗ)
- 🚗 **Xe**: 51A-12345 (Số sàn)
- 📊 **Trình độ**: Sơ cấp (smart grouping!)
- ✅ Xác nhận

#### Bước 3: Xem Chi Tiết Học Viên
1. Click vào một ca dạy có 1 học viên đã đặt
2. **Kỳ vọng**: Thấy avatar/indicator 1 học viên (1 chấm xanh, 2 chấm xám)
3. Có thể thấy tên + trình độ của học viên

---

### **Phase 3: Admin Xem Dự Báo & Quản Lý (5 phút)**

#### Bước 1: Đăng nhập Admin
1. **Logout** → Đăng nhập: `admin@sds.vn` / `admin123`
2. **Kỳ vọng**: Admin Dashboard

```
✨ Smart Booking: Tự động ghép học viên cùng trình độ, 
                 tối ưu hóa lịch, quản lý tín chỉ.

📊 Smart Forecast: Dự báo 8 tuần, so sánh năng lực GV, 
                   cảnh báo nếu thiếu.
```

#### Bước 2: Xem Biểu Đồ Dự Báo
1. **Top section**: "Dự báo nhu cầu đặt lịch"
2. **Biểu đồ**: So sánh "Dự báo đặt lịch" vs "Năng lực GV" trong 4 tuần
3. **Kỳ vọng**: 
   - Nếu dự báo > năng lực: Tuần đó có 🔴 **cảnh báo** ⚠️
   - Nếu dự báo ≤ năng lực: Tuần đó ✅ **OK**

```
Tuần 2026-18: Dự báo 12 | Năng lực: 45 ✅
Tuần 2026-19: Dự báo 14 | Năng lực: 45 ✅
Tuần 2026-20: Dự báo 16 | Năng lực: 45 ✅
```

#### Bước 3: Xem & Override Sessions
1. Scroll xuống "Danh sách lịch học"
2. Xem 20 sessions với:
   - 👨‍🏫 Giáo viên
   - ⏰ Thời gian
   - 🚗 Xe
   - 👥 Số học viên đã đặt / tổng
   - ✅ Status (confirmed)
3. Click một session → Modal "Cập nhật ca học"
4. Có thể:
   - ✏️ Đổi giáo viên
   - ❌ Hủy ca (status → cancelled)
5. Click "Lưu thay đổi"
6. **Kỳ vọng**: Cập nhật thành công!

---

## 💬 Demo Chatbot + RAG (3 phút)

### **Kích hoạt Chat**
1. Đăng nhập lại với `learner1@sds.vn`
2. **Bottom right**: Click nút 💬 để mở chat
3. **Welcome**: "Xin chào! Tôi là trợ lý AI của SDS. Tôi có thể giúp gì cho bạn?"

### **Test Intent Detection**

#### Booking Query
```
👤 User: "Lịch học của tôi là lúc mấy?"
🤖 Bot: (Gọi /bookings/me → hiển thị lịch học)
```

#### Fee Query
```
👤 User: "Tôi có bao nhiêu tín chỉ?"
🤖 Bot: (RAG retrieves từ KB → trả lời)
```

#### General FAQ
```
👤 User: "Xe nào ở trường?"
🤖 Bot: (RAG retrieval → trả lời từ Knowledge Base)
```

### **API Rate Limit Demo** (Khi API key hết limit)
```
🤖 Bot: "🔄 Hệ thống đang bận. Vui lòng chọn một trong các câu hỏi thường gặp dưới đây..."

📌 Câu hỏi thường gặp:
   1. "Làm sao để đặt lịch học?"
   2. "Tôi có bao nhiêu tín chỉ?"
   3. "Tôi có thể hủy lịch không?"

👤 User: Click "Làm sao để đặt lịch học?"
⚡ Bot: (Loading 1.2s) → Phản hồi mẫu + "⚡ Phản hồi tự động"
```

---

## ✅ Checklist Demo

### Learner Dashboard
- [ ] Hiển thị 10 tín chỉ
- [ ] Hiển thị buổi học tiếp theo (nếu có)
- [ ] Smart Booking info card
- [ ] Lịch học gần đây

### Booking Flow
- [ ] Filter ca học theo ngày
- [ ] Hiển thị best_match_score (Phù hợp cao/vừa/thấp)
- [ ] Đặt lịch thành công → trừ tín chỉ
- [ ] Cập nhật lịch /bookings/me

### Instructor Schedule
- [ ] Fix week format bug (YYYY-WW)
- [ ] Hiển thị lịch dạy theo tuần
- [ ] Smart Grouping info card
- [ ] Hiển thị số học viên + trình độ

### Admin Dashboard
- [ ] Smart Booking + Smart Forecast info
- [ ] Biểu đồ dự báo 4 tuần
- [ ] Cảnh báo ⚠️ nếu thiếu năng lực
- [ ] Override ca học (đổi GV hoặc hủy)

### Chatbot (API có sẵn)
- [ ] Welcome message
- [ ] Intent detection: booking_query
- [ ] Intent detection: general_faq
- [ ] Escalate button

### Chatbot (API Rate Limit)
- [ ] Detect API limit error
- [ ] Hiển thị suggested_questions
- [ ] Mock response với loading effect (1.2s)
- [ ] Phản hồi mẫu có tag "⚡ Phản hồi tự động"

---

## 🔧 Tấn công Bugs (Nếu Demo Fails)

### Bug 1: Week Format "Invalid week format. Use YYYY-WW"
**Nguyên nhân**: `<input type="week">` trả về `2026-W18` chứ không phải `2026-18`
**Fix**: ✅ Đã fix bằng cách convert `-W` → `-` ở frontend

### Bug 2: Ca học không hiện
**Kiểm tra**:
```bash
# 1. DB có dữ liệu sessions?
SELECT COUNT(*) FROM sessions;

# 2. Sessions có slot_start trong tuần tới?
SELECT * FROM sessions 
WHERE slot_start >= NOW() + INTERVAL '2 days'
LIMIT 5;

# 3. Seed data đầy đủ?
docker-compose exec backend python -m app.scripts.seed
```

### Bug 3: Matching score luôn là 0
**Kiểm tra**:
```python
# booking_service.py - get_available_slots()
# Tính best_match_score dựa trên:
# - Learner skill_level
# - Learner count cùng skill level in slot
```

### Bug 4: Chat không kết nối
**Kiểm tra**:
```bash
# 1. GEMINI_API_KEY có set?
cat .env | grep GEMINI_API_KEY

# 2. Chat endpoint có lỗi?
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test", "message": "xin chào"}'
```

---

## 📊 Dữ Liệu Seed Được Tạo

**Người dùng**: 10 learners + 3 instructors + 1 admin + 1 support = 15 users
**Xe**: 5 xe (3 số sàn + 2 số tự động)
**Sessions**: 54 sessions (3 tuần × 6 ngày × 3 ca/ngày)
**Past Sessions**: 12 sessions (dữ liệu lịch sử cho forecast)
**Bookings**: 50+ bookings (phân tán đều)

---

## 🎯 Success Criteria

✅ **Luồng Hoàn Chỉnh**:
1. Học viên đặt lịch → thấy best_match_score
2. Giáo viên xem lịch dạy → thấy học viên cùng level
3. Admin xem dự báo → có cảnh báo nếu thiếu
4. Chat respond → có RAG hoặc mock khi API limit

✅ **Hiệu Năng**:
- Trang load < 2s
- Chat response < 5s
- Biểu đồ render mượt

✅ **Smart Features**:
- Matching score tính đúng
- Grouping tối ưu (cùng level)
- Forecast dự báo chính xác
- API limit handling graceful

---

