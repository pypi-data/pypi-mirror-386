import click
import subprocess
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

ENV_FILE = os.path.join(os.path.expanduser("~"), ".buxcli.env")


def setup_env():
    """Prompt user for email credentials if not set up yet"""
    if not os.path.exists(ENV_FILE):
        print("🔧 First-time setup: Configure your email notifications.")
        mail_id = input("Enter your Gmail address: ").strip()
        password = input("Enter your App Password: ").strip()
        with open(ENV_FILE, "w") as f:
            f.write(f"MAIL_ID={mail_id}\n")
            f.write(f"EMAIL_API_KEY={password}\n")
        print("✅ Credentials saved! You won’t need to enter them again.\n")


def load_env():
    load_dotenv(ENV_FILE)
    return os.getenv("MAIL_ID"), os.getenv("EMAIL_API_KEY")


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


def run_command(command_list):
    mail_id, password = load_env()
    command = " ".join(command_list)
    click.echo(f"🚀 Running: {command}\n")

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


@click.group(invoke_without_command=True)
@click.argument("cmd", nargs=-1)
@click.pass_context
def cli(ctx, cmd):
    """buxcli - Run commands and get email notifications"""
    setup_env()

    if ctx.invoked_subcommand is None and not cmd:
        # No subcommand or args: show ASCII art / intro
        click.echo(r"""

Welcome to buxcli! 🚀

Run commands with automatic email notifications when they succeed, fail, or a server starts.

Example:
  buxcli run "python manage.py runserver"
        """)
    elif cmd:
        # If raw command passed
        run_command(cmd)


@cli.command()
@click.argument("cmd", nargs=-1)
def run(cmd):
    """Run any shell command with email notifications"""
    run_command(cmd)


if __name__ == "__main__":
    cli()
