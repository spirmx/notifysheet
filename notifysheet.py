import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta
import time

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)

sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1N7YEZvtaJkKY8z8GjZn9gTDwFL1-f0xP1iwAVWo1OBQ/edit?usp=sharing")
contract_sheet = sheet.worksheet("Contract")
usermail_sheet = sheet.worksheet("USERMAIL")

rows = contract_sheet.get_all_records()  # ดึงข้อมูลจากตาราง Contract
emails = usermail_sheet.col_values(1)[1:]  # ดึงอีเมลจากคอลัมน์ A ของแผ่นงาน USERMAIL (ข้าม header)

# Email Config (ใช้จาก GitHub Secrets)
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# ฟังก์ชันส่งอีเมล
def send_email(to, subject, message):
    msg = MIMEMultipart()
    msg["From"] = "แจ้งเตือนระบบ <noreply@example.com>"  # แสดงชื่อเท่านั้น
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to, msg.as_string())

# ตรวจสอบค่า DaysRemaining และส่งอีเมลแจ้งเตือน
def check_and_send_notifications():
    now = datetime.now()
    for row in rows:
        try:
            days_remaining = int(row.get("DaysRemaining", 999))  # ใช้ DaysRemaining จากตาราง
        except:
            continue

        if days_remaining in [5, 3, 1, 0]:  # ตรวจสอบว่าค่า DaysRemaining เป็น 5, 3, 1 หรือ 0
            contract_id = row["ContractID"]
            disname = row["DISNAME"]
            start_date = row["Starting-date"]
            end_date = row["Ending-date"]
            pdf = row["PDFfile"]

            subject = f"แจ้งเตือนสัญญา {contract_id} เหลืออีก {days_remaining} วัน"
            body = f"""เรียนผู้ดูแล,

สัญญาเลขที่ {contract_id} ของ {disname} กำลังจะหมดอายุในอีก {days_remaining} วัน

📅 เริ่มต้น: {start_date}
📅 สิ้นสุด: {end_date}
📄 เอกสารแนบ: {pdf}

กรุณาตรวจสอบหรือดำเนินการต่อไปตามระบบ

ขอบคุณครับ/ค่ะ
ระบบแจ้งเตือนสัญญา"""

            # ส่งอีเมลให้กับแอดมินทั้งหมด
            for email in emails:
                send_email(email, subject, body)

# ฟังก์ชันคำนวณเวลาให้เริ่มตั้งแต่ 7 โมงเช้า
def wait_until_seven_am():
    now = datetime.now()
    target_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if now > target_time:
        target_time += timedelta(days=1)
    wait_time = (target_time - now).seconds
    time.sleep(wait_time)

# ฟังก์ชันหลักที่จะรันทุก 4 ชั่วโมง
def run_every_4_hours():
    while True:
        # เริ่มทำงานทุกครั้งที่ถึงเวลา 7 โมงเช้า
        wait_until_seven_am()

        # ตรวจสอบและส่งการแจ้งเตือน
        check_and_send_notifications()

        # รอ 4 ชั่วโมงก่อนจะทำงานอีกครั้ง
        time.sleep(4 * 3600)

# เริ่มทำงาน
if __name__ == "__main__":
    run_every_4_hours()
