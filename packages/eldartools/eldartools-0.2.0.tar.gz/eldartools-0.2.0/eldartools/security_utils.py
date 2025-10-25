import random, string

def generate_password(length=12, symbols=True, numbers=True):
    letters = string.ascii_letters
    digits = string.digits if numbers else ""
    special = "!@#$%^&*()-_=+[]{};:,.<>?" if symbols else ""
    all_chars = letters + digits + special
    if not all_chars:
        raise ValueError("No characters selected!")
    return "".join(random.choice(all_chars) for _ in range(length))
def generate_strong_password(length=20):
    import string, random
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.<>?"
    return "".join(random.choice(all_chars) for _ in range(length))

def check_strength(password):
    import re
    score = 0
    if len(password)>=8: score+=1
    if re.search(r"[A-Z]",password): score+=1
    if re.search(r"[a-z]",password): score+=1
    if re.search(r"[0-9]",password): score+=1
    if re.search(r"[!@#$%^&*()-_=+\[\]{};:,.<>?]",password): score+=1
    return score # 0-5

def hash_text(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()

def verify_hash(text, hash_value):
    return hash_text(text) == hash_value
