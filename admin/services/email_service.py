import aiosmtplib
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM


async def send_verification_email(to_email: str, code: str):
    body = f"您的验证码是：{code}，5分钟内有效。请勿将验证码透露给他人。"

    # 开发模式：无 SMTP 配置时打印到控制台
    is_dev = (not SMTP_USER) and SMTP_HOST in ("localhost", "127.0.0.1")
    if is_dev:
        print("\n" + "=" * 50)
        print(f"  DEV MODE - 验证码")
        print(f"  To:   {to_email}")
        print(f"  Code: {code}")
        print("=" * 50 + "\n")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "LLM Gateway 邮箱验证码"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
        use_tls=True,
    )
