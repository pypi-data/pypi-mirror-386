import click
import smtplib
from email.mime.text import MIMEText



def send_email(mail_id, password, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = mail_id
    msg["To"] = mail_id
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(mail_id, password)
            s.send_message(msg)
        click.echo(click.style(f"\n📩 Email sent: {subject}", fg="cyan", bold=True))
    except Exception as e:
        click.echo(click.style(f"\n⚠️ Failed to send email: {e}", fg="red", bold=True))



def verify_email_credentials(mail_id, password):
    """Send a small test email to verify credentials"""
    try:
        msg = MIMEText("✅ This is a test email from buxcli to verify your credentials.")
        msg["Subject"] = "buxcli Email Verification"
        msg["From"] = mail_id
        msg["To"] = mail_id
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(mail_id, password)
            s.send_message(msg)
        click.echo(click.style("📩 Test email sent successfully!", fg="cyan", bold=True))
        return True
    except Exception as e:
        click.echo(click.style(f"⚠️ Email verification failed: {e}", fg="red", bold=True))
        return False
