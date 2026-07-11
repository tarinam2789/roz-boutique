import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Add email imports
old_imports = "from werkzeug.utils import secure_filename"
new_imports = (
    "from werkzeug.utils import secure_filename\n"
    "import smtplib\n"
    "from email.message import EmailMessage"
)
if "import smtplib" not in content:
    content = content.replace(old_imports, new_imports, 1)
    print("Added email imports.")
else:
    print("Email imports already present — skipped.")

# 2. Add SMTP config + send_contact_email function, right before app = Flask(__name__)
smtp_block = '''
# ------------------------------------------------------------- email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = ""  # e.g. "tarinaafrozmuna@gmail.com"
SMTP_PASSWORD = ""  # the 16-character Gmail App Password, no spaces
NOTIFY_EMAIL = "tarinaafrozmuna@gmail.com"


def send_contact_email(name, email, subject, message):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Roz Boutique contact form: {subject or \\'New message\\'}"
        msg["From"] = SMTP_USERNAME
        msg["To"] = NOTIFY_EMAIL
        msg["Reply-To"] = email
        msg.set_content(
            f"New message from your Roz Boutique contact form.\\n\\n"
            f"Name: {name}\\n"
            f"Email: {email}\\n"
            f"Subject: {subject or \\'(no subject)\\'}\\n\\n"
            f"Message:\\n{message}\\n\\n"
            f"---\\nReply directly to this email to respond to {name}."
        )
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[email] Failed to send contact notification: {e}")
        return False


'''

if "def send_contact_email" not in content:
    content = content.replace("app = Flask(__name__)", smtp_block + "app = Flask(__name__)", 1)
    print("Added SMTP config and send_contact_email function.")
else:
    print("send_contact_email already present — skipped.")

# 3. Call send_contact_email() right after the message is saved to the database
old_save = '''        execute_db(
            "INSERT INTO contact_messages (name, email, subject, message) VALUES (?,?,?,?)",
            (name, email, subject, message),
        )
        flash("Thank you'''
new_save = '''        execute_db(
            "INSERT INTO contact_messages (name, email, subject, message) VALUES (?,?,?,?)",
            (name, email, subject, message),
        )
        send_contact_email(name, email, subject, message)
        flash("Thank you'''

if "send_contact_email(name, email, subject, message)" not in content:
    if old_save in content:
        content = content.replace(old_save, new_save, 1)
        print("Wired send_contact_email() into the /contact route.")
    else:
        print("WARNING: could not find the contact route save block — email sending was NOT wired in. Contact support.")
else:
    print("Contact route already wired — skipped.")

with open("app.py", "w") as f:
    f.write(content)

print("\nDone. Now run: python3 -c \"import ast; ast.parse(open('app.py').read()); print('app.py is valid!')\"")
