"""
SMS 인증번호 발송 유틸리티

현재: 콘솔에 인증번호를 출력합니다 (개발용).
프로덕션: CoolSMS, NHN Cloud, Twilio 등 실제 SMS API로 교체하세요.

예시 (CoolSMS):
  pip install coolsms-python-sdk
  from coolsms_kakao import Message
"""
import os


def send_verification_sms(phone_number: str, verify_code: str) -> bool:
    """
    인증번호를 SMS로 발송합니다.
    개발 환경에서는 서버 콘솔에 출력합니다.
    """
    print("=" * 50)
    print(f"[SMS 인증] 수신번호: {phone_number}")
    print(f"[SMS 인증] 인증코드: {verify_code}")
    print("=" * 50)

    # TODO: 실제 SMS 서비스 연동 시 아래 주석을 해제하고 위 print를 제거
    # ──────────────────────────────────────────────
    # CoolSMS 예시:
    # from coolsms_kakao import Message
    # message = Message(
    #     api_key=os.getenv("COOLSMS_API_KEY"),
    #     api_secret=os.getenv("COOLSMS_API_SECRET"),
    # )
    # message.add_message(
    #     to=phone_number,
    #     from_=os.getenv("COOLSMS_SENDER"),
    #     text=f"[필기→문서 변환기] 인증번호: {verify_code}",
    # )
    # result = message.send()
    # ──────────────────────────────────────────────

    return True
