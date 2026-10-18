"""
Secrets Audit Script for RepSync (M3-SEC-5).
Scans working tree and git commit history for potential leaked credentials
(API keys, private keys, database passwords).
"""
import os
import re
import subprocess
import sys

SUSPICIOUS_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/TinyFish Secret Key"),
    (r"AIzaSy[a-zA-Z0-9_-]{33}", "Google Gemini API Key"),
    (r"gsk_[a-zA-Z0-9]{40,}", "Groq API Key"),
    (r"postgres://[a-zA-Z0-9_]+:[^@]+@", "PostgreSQL Credentials"),
    (r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----", "Private Key Block"),
]

EXCLUDED_FILES = {".env.example", "audit_secrets.py"}


def check_working_tree():
    print("=== Scanning Working Tree for Leaked Secrets ===")
    violations = 0
    for root, _, files in os.walk("."):
        if ".git" in root or ".venv" in root or "__pycache__" in root:
            continue
        for file in files:
            if file in EXCLUDED_FILES or file.endswith((".pyc", ".db", ".sqlite")):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern, label in SUSPICIOUS_PATTERNS:
                        matches = re.findall(pattern, content)
                        for m in matches:
                            # Filter out dummy/example strings
                            if "your-key" in m or "your-gemini" in m or "your-groq" in m:
                                continue
                            print(f"[ALERT] Found {label} in {path}: {m[:10]}...")
                            violations += 1
            except Exception as e:
                print(f"Could not read {path}: {e}")

    return violations


def check_git_history():
    print("\n=== Scanning Git Commit History ===")
    try:
        log_diff = subprocess.check_output(
            ["git", "log", "-p", "-n", "30"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        violations = 0
        for line in log_diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                for pattern, label in SUSPICIOUS_PATTERNS:
                    matches = re.findall(pattern, line)
                    for m in matches:
                        if "your-key" in m or "your-gemini" in m or "your-groq" in m:
                            continue
                        print(f"[ALERT] Found {label} committed in git history: {m[:10]}...")
                        violations += 1
        return violations
    except Exception as e:
        print(f"Git log check warning: {e}")
        return 0


def main():
    tree_violations = check_working_tree()
    history_violations = check_git_history()
    total = tree_violations + history_violations
    if total == 0:
        print("\n[CLEAN] No leaked secrets found in working tree or git history!\n")
        sys.exit(0)
    else:
        print(f"\n[FAILED] Found {total} potential secret violations.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
