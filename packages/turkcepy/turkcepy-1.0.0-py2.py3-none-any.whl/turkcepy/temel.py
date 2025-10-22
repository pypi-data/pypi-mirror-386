
# turkcepy/temel.py

def yaz(*args, **kwargs):
    """Print fonksiyonunun Türkçe versiyonu"""
    print(*args, **kwargs)

def al(mesaj=""):
    """Input fonksiyonunun Türkçe versiyonu"""
    return input(mesaj)

def bekle(saniye):
    """Sleep fonksiyonunun Türkçe versiyonu"""
    import time
    time.sleep(saniye)

def rastgele(min_deger=0, max_deger=1):
    """Rastgele sayı üretir"""
    import random
    if isinstance(min_deger, int) and isinstance(max_deger, int):
        return random.randint(min_deger, max_deger)
    else:
        return random.uniform(min_deger, max_deger)