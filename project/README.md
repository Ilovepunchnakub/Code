# ⚔️ Coding Arena Discord Bot (ไทย)

บอท Discord สำหรับเรียนเขียนโค้ดแบบเกม RPG พร้อมระบบแอดมินจัดการโจทย์จากมือถือ

## ✅ สถานะระบบล่าสุด

- ใช้ **Local Smart Judge** (ไม่พึ่ง API execute ภายนอกเป็นค่าเริ่มต้น)
- รองรับ schema โจทย์ใหม่:
  - `xp`, `main_answer`, `alt_answers`, `show_solution`, `daily_limit`, `bonus_first_try_xp`, `output_example`, `tags`
- คำสั่งแอดมินแบบไทย:
  - `/เพิ่มโจทย์` (3 หน้า)
  - `/แก้ไขโจทย์`
  - `/ลบโจทย์`
- รองรับตั้งค่า env ยืดหยุ่น:
  - `DISCORD_TOKEN` หรือ `DISCORD_BOT_TOKEN` หรือ `BOT_TOKEN`

---

## 🚀 Quick Start

```bash
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## ⚙️ ENV ที่รองรับ

ดูตัวอย่างเต็มใน `.env.example`

- `DISCORD_TOKEN` (แนะนำ)
- `DISCORD_BOT_TOKEN`
- `BOT_TOKEN`
- `APP_ENV=development|staging|production`
- `AUTO_SYNC_COMMANDS=true|false`
- `BOT_DATA_DIR=./`

---

## 📚 คำสั่งหลัก

### ผู้เรียน
- `/learn` หรือ `/เรียน`
- `/progress`
- `/daily`
- `/shop`
- `/profile`
- `/rank`

### แอดมิน
- `/adminpanel`
- `/เพิ่มโจทย์`
- `/แก้ไขโจทย์`
- `/ลบโจทย์`

---

## 🧩 โครงสร้างโจทย์ (แนะนำ)

```json
{
  "title": "Hello World",
  "xp": 20,
  "difficulty": "ง่าย",
  "description": "ให้เขียนโปรแกรมแสดงคำว่า Hello World",
  "hint": "ใช้ printf()",
  "main_answer": "...",
  "alt_answers": ["...", "..."],
  "show_solution": true,
  "daily_limit": 0,
  "bonus_first_try_xp": 10,
  "output_example": "Hello World",
  "tags": ["printf", "พื้นฐาน"]
}
```

---

## 🛠️ การย้ายเครื่อง / ย้ายโฮสต์

1. ย้ายโฟลเดอร์ `project/` ทั้งหมด
2. ตั้ง env เหมือนเดิม (`.env`)
3. ถ้าต้องการย้าย data ไป path ใหม่ ให้ตั้ง `BOT_DATA_DIR`
4. รัน `python main.py`

ระบบจะตรวจและสร้างไฟล์ที่จำเป็น (`assignments.json`, `users.json`) อัตโนมัติใน startup

---

## 🧪 Testing

```bash
cd project
pytest -q
```

---

## 📝 หมายเหตุ

- README นี้อัปเดตให้สอดคล้องกับระบบใหม่แล้ว (ตัดคู่มือ Piston API เดิมออก)
- สำหรับ production แนะนำเปิด log aggregation และ backup `assignments.json`/`users.json` ตามรอบเวลา
