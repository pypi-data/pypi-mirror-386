import random
import string

def generate(length=12, symbols=True, numbers=True):
    """
    Güclü parol generatoru.
    Parametrlər:
        length (int): parol uzunluğu (defolt 12)
        symbols (bool): simvol əlavə edilsin?
        numbers (bool): rəqəmlər əlavə edilsin?
    """
    letters = string.ascii_letters
    digits = string.digits if numbers else ""
    special = "!@#$%^&*()-_=+[]{};:,.<>?" if symbols else ""

    all_chars = letters + digits + special
    if not all_chars:
        raise ValueError("Heç bir simvol seçilməyib!")

    password = ''.join(random.choice(all_chars) for _ in range(length))
    return password
