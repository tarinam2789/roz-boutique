"""
Used as the Render build step instead of seed.py directly.
Only creates/seeds the database if it doesn't already exist yet, so that
redeploying your code doesn't wipe out products or orders you've added
through the live admin panel.

To reset your live database back to the demo data on purpose, delete this
file's check by running seed.py directly instead (or just delete roz.db
before deploying).
"""
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roz.db")

if os.path.exists(DB_PATH):
    print(f"roz.db already exists at {DB_PATH} — skipping seed, keeping existing data.")
else:
    print("No existing roz.db found — running seed.py to create it.")
    import subprocess
    subprocess.run(["python3", "seed.py"], check=True)
