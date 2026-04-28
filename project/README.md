# ⚔️ Discord Coding Arena Bot

บอท Discord สำหรับระบบเรียนเขียนโปรแกรม + เกม RPG + Admin Panel (รองรับมือถือ)

## ฟีเจอร์ใหม่
- Achievement 100 แบบ (เริ่มต้น/ต่อเนื่อง/C/Python/ความยาก/ทักษะ/พิเศษ)
- Daily Reward 7 วัน + Weekly Jackpot แบบสุ่ม
- `/profile` แบบเกม พร้อมปุ่ม เปลี่ยนธีม / ดู Badge / สถิติ / ดูอันดับ
- `/rank` มีหมวด รวม / Python / C / Streak / Coins / Accuracy
- `/learn` flow ครบ: Language -> Chapter -> Task -> Submit + Hint + Example

## คำสั่งหลัก
- `/learn`
- `/profile`
- `/progress`
- `/rank`
- `/daily`
- `/shop`
- `/adminpanel` (Admin)

## ติดตั้ง
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ใส่ Token และรัน
```bash
export DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
python main.py
```

## Deploy Railway
1. Push โปรเจกต์ขึ้น GitHub
2. ไป Railway > New Project > Deploy from GitHub
3. ตั้ง Environment Variable: `DISCORD_TOKEN`
4. Start command: `python main.py`

## อัป GitHub ผ่านมือถือ
1. ใช้แอป GitHub หรือ Termux
2. สร้าง repo ใหม่และ push โค้ด
3. เชื่อม repo นี้กับ Railway ได้ทันที

## เพิ่มโจทย์ภายหลัง
- ใช้ `/adminpanel` > `➕ เพิ่มโจทย์`
- หรือแก้ไฟล์ `assignments.json`
