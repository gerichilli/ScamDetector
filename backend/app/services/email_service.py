from email.message import EmailMessage
import smtplib

from app.core.config import get_settings


def smtp_enabled() -> bool:
    settings = get_settings()
    return all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.smtp_sender_email,
        ]
    )


def send_trusted_contact_confirmation_email(target_email: str, target_name: str, confirmation_url: str) -> bool:
    settings = get_settings()
    if not smtp_enabled():
        return False

    message = EmailMessage()
    message["Subject"] = "Xac nhan nguoi lien he tin cay"
    sender_name = settings.smtp_sender_name or settings.app_name
    message["From"] = f"{sender_name} <{settings.smtp_sender_email}>"
    message["To"] = target_email
    message.set_content(
        "\n".join(
            [
                f"Chao {target_name},",
                "",
                "Ban da duoc them lam nguoi lien he tin cay trong he thong canh bao lua dao.",
                "Neu ban dong y nhan thong bao khi co canh bao rui ro cao, vui long mo lien ket ben duoi de xac nhan:",
                confirmation_url,
                "",
                "Neu ban khong mong muon nhan thong bao, vui long bo qua email nay.",
            ]
        )
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return True


def send_trusted_contact_alert_email(
    target_email: str,
    target_name: str,
    elderly_name: str,
    phone_number: str,
    risk_level: str,
    message: str,
    recommended_action: str,
) -> bool:
    settings = get_settings()
    if not smtp_enabled():
        return False

    risk_label = risk_level.upper()
    message_obj = EmailMessage()
    message_obj["Subject"] = f"Canh bao khan: cuoc goi rui ro {risk_label}"
    sender_name = settings.smtp_sender_name or settings.app_name
    message_obj["From"] = f"{sender_name} <{settings.smtp_sender_email}>"
    message_obj["To"] = target_email
    message_obj.set_content(
        "\n".join(
            [
                f"Chao {target_name},",
                "",
                f"He thong vua ghi nhan mot canh bao rui ro {risk_label} cho {elderly_name}.",
                f"So dien thoai nghi ngo: {phone_number}",
                f"Canh bao: {message}",
                f"Khuyen nghi: {recommended_action}",
                "",
                "Bac vui long lien he lai de xac minh va ho tro kip thoi.",
            ]
        )
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message_obj)
    return True
