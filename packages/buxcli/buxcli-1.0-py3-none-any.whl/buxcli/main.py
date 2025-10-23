import click, subprocess, smtplib, os, time
from email.mime.text import MIMEText
from dotenv import load_dotenv

ENV_FILE = os.path.join(os.path.expanduser("~"), ".buxcli.env")

def setup_env():
    """Prompt user for email credentials if not set up yet"""
    if not os.path.exists(ENV_FILE):
        print("🔧 First-time setup: Let's configure your email notification settings.")
        mail_id = input("Enter your Gmail address: ").strip()
        password = input("Enter your App Password (from Google App Passwords): ").strip()

        with open(ENV_FILE, "w") as f:
            f.write(f"MAIL_ID={mail_id}\n")
            f.write(f"EMAIL_API_KEY={password}\n")

        print("✅ Credentials saved! You won’t need to enter them again.\n")

def load_env():
    load_dotenv(ENV_FILE)
    return os.getenv("MAIL_ID"), os.getenv("EMAIL_API_KEY")

@click.command()
@click.argument('cmd', nargs=-1)
# now cmd=("python","manage.py","runserver")

def cli(cmd):
    setup_env()
    mail_id, password = load_env()

    command = " ".join(cmd)
    click.echo(f"🚀 Running: {command}\n")

    # Run command and capture output in real-time
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    server_started = False
    keywords = [
        "starting development server at",
        "running on http://",
        "listening on",
        "application started",
    ]

    try:
        for line in process.stdout:
            print(line, end="")
            if any(keyword in line.lower() for keyword in keywords) and not server_started:
                server_started = True
                send_email(mail_id, password, "🚀 Server Started", f"{command} started successfully!")
        
        process.wait()

        if process.returncode == 0 and not server_started:
            send_email(mail_id, password, "✅ Success", f"Command succeeded: {command}")
        elif process.returncode != 0:
            send_email(mail_id, password, "❌ Failure", f"Command failed: {command}")
    
    except KeyboardInterrupt:
        print("\n🛑 Command interrupted by user.")
        process.terminate()
        send_email(mail_id, password, "🛑 Interrupted", f"Command interrupted: {command}")

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
        print(f"\n📩 Email sent: {subject}")
    except Exception as e:
        print(f"\n⚠️ Failed to send email: {e}")

if __name__ == '__main__':
    cli()
