# ⚔️ Discord Coding Arena Bot

บอท Discord ระบบเรียนเขียนโปรแกรม + RPG + Admin Panel (รองรับมือถือ)

## ไฮไลต์ที่แก้แล้ว
- Judge ใหม่: รองรับ C/Python, ชื่อไฟล์ถูกต้อง (`main.c`, `main.py`), เทียบคำตอบแบบ smart, รองรับ Compile/Runtime/WA/TLE/Memory/Keyword checks
- Admin Panel ใหม่: เพิ่ม/แก้/ลบโจทย์สะดวกขึ้น, แก้แบบทีละ field
- เพิ่มโจทย์แบบ 3 หน้า Modal: ข้อมูลหลัก -> รายละเอียด -> ตั้งค่า Judge
- รองรับ assignments schema ใหม่ (`required_keywords`, `forbidden_keywords`, `time_limit`, `memory_limit`)

## คำสั่งหลัก
- `/learn`
- `/progress`
- `/profile`
- `/rank`
- `/daily`
- `/shop`
- `/adminpanel` (เฉพาะ Admin)

## วิธีวางไฟล์
วางตามโครงสร้างนี้:
- `project/main.py`
- `project/cogs/*.py`
- `project/views/*.py`
- `project/utils/*.py`
- `project/assignments.json`
- `project/users.json`

## ติดตั้งและรัน
```bash
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DISCORD_TOKEN="YOUR_TOKEN"
python main.py
```

## Deploy Railway
1. Push โค้ดขึ้น GitHub
2. Railway -> New Project -> Deploy from GitHub
3. ตั้ง ENV: `DISCORD_TOKEN`
4. Start Command: `python main.py`
5. เลือกเป็น Worker/Background Service

## ใช้งานมือถือ
- ใช้ Slash Commands + Buttons + Dropdown + Modal ได้ใน Discord Mobile โดยตรง
- Admin เพิ่มโจทย์ได้จากมือถือผ่าน `/adminpanel`


## อัปเกรดล่าสุด (Reliability)
- เพิ่ม **Automated Tests**: unit/integration/snapshot ใน `project/tests`
- เพิ่ม **Judge Queue/Worker** กัน burst traffic
- เพิ่ม **Admin Audit Log** ที่ไฟล์ `project/admin_audit.log` พร้อม undo ล่าสุด
- เพิ่ม Admin UX: preview diff ก่อนบันทึก, duplicate task, bulk import/export chapter

### รันเทสต์
```bash
cd project
pytest -q
```


## แก้ปัญหา Piston 401 Unauthorized
หากเจอข้อความ `Unauthorized` ตอนตรวจโค้ด ให้ตั้งค่า ENV ตามผู้ให้บริการของคุณ:

```bash
export PISTON_URL="https://your-piston-host/api/v2/execute"
export PISTON_API_TOKEN="your_token"
# optional
export PISTON_AUTH_HEADER="Authorization"
export PISTON_AUTH_SCHEME="Bearer"
```

รองรับหลาย endpoint ได้ด้วย:
```bash
export PISTON_URLS="https://host1/api/v2/execute,https://host2/api/v2/execute"
```
