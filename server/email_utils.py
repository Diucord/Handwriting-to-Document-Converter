import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def send_verification_email(to_email: str, verify_code: str) -> bool:
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:
        print("[ERROR] SMTP_EMAIL 또는 SMTP_PASSWORD 환경변수가 설정되지 않았습니다.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[필기→문서 변환기] 이메일 인증 코드"
    msg["From"] = smtp_email
    msg["To"] = to_email

    html = f"""\
    <html>
    <body style="font-family: 'Noto Sans KR', sans-serif; padding: 20px;">
        <h2 style="color: #3b82f6;">이메일 인증 코드</h2>
        <p>회원가입을 완료하려면 아래 인증 코드를 입력해주세요.</p>
        <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px;
                    font-size: 32px; font-weight: bold; text-align: center;
                    letter-spacing: 8px; margin: 20px 0; color: #3b82f6;">
            {verify_code}
        </div>
        <p style="color: #6b7280;">이 코드는 회원가입 완료에 필요합니다.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] 인증 이메일 전송 실패: {e}")
        return False


def send_temp_password_email(to_email: str, temp_password: str) -> bool:
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:
        print("[ERROR] SMTP_EMAIL 또는 SMTP_PASSWORD 환경변수가 설정되지 않았습니다.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[필기→문서 변환기] 임시 비밀번호 안내"
    msg["From"] = smtp_email
    msg["To"] = to_email

    html = f"""\
    <html>
    <body style="font-family: 'Noto Sans KR', sans-serif; padding: 20px;">
        <h2 style="color: #3b82f6;">임시 비밀번호 안내</h2>
        <p>요청하신 임시 비밀번호입니다.</p>
        <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px;
                    font-size: 24px; font-weight: bold; text-align: center;
                    letter-spacing: 4px; margin: 20px 0;">
            {temp_password}
        </div>
        <p style="color: #6b7280;">로그인 후 반드시 비밀번호를 변경해주세요.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] 이메일 전송 실패: {e}")
        return False
