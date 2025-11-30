
import os

def check_file(filename):
    print(f"--- Checking {filename} ---")
    if not os.path.exists(filename):
        print("File not found.")
        return
        
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "SMTP_PASS" in line:
                print(f"Found: {line.strip()}")

check_file(".env")
check_file(".env.python")
