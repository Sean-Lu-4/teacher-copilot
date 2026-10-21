"""Optional SMTP delivery. Secrets stay in environment variables."""
import os
import smtplib
import ssl
from email.message import EmailMessage


def available():
    return bool(os.getenv('CSA_SMTP_USER') and os.getenv('CSA_SMTP_PASSWORD'))


def send_code(address, code):
    if not available():
        raise ValueError('邮箱服务尚未启用，请使用账号恢复码。')
    message = EmailMessage()
    message['Subject'] = 'CSA Studio 账号验证码'
    message['From'] = os.environ['CSA_SMTP_USER']
    message['To'] = address
    message.set_content(f'你的验证码是 {code}，10 分钟内有效。请勿向他人提供。\n如果不是你本人操作，请忽略此邮件。')
    try:
        with smtplib.SMTP_SSL(os.getenv('CSA_SMTP_HOST', 'smtp.163.com'),
                              int(os.getenv('CSA_SMTP_PORT', '465')),
                              timeout=15, context=ssl.create_default_context()) as smtp:
            smtp.login(os.environ['CSA_SMTP_USER'], os.environ['CSA_SMTP_PASSWORD'])
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        raise ValueError('验证码暂时发送失败，请稍后重试或使用恢复码。') from None
