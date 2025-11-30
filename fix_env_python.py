
import os

file_path = ".env.python"
old_pass = "ntwb bedy skvd bhnt"
new_pass = "yavb xvqd ucyk xfth"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if old_pass in content:
        new_content = content.replace(old_pass, new_pass)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully updated password in .env.python")
    else:
        print("Old password not found in .env.python. Appending new one...")
        # If not found, just append
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\nSMTP_PASS={new_pass}\n")
        print("Appended SMTP_PASS to .env.python")

except Exception as e:
    print(f"Error updating .env.python: {e}")
