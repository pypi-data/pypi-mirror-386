
# turkcepy/matematik.py

def mat_topla(a, b):
    """Toplama işlemi"""
    return a + b

def mat_cikar(a, b):
    """Çıkarma işlemi"""
    return a - b

def mat_carp(a, b):
    """Çarpma işlemi"""
    return a * b

def mat_bol(a, b):
    """Bölme işlemi"""
    if b == 0:
        raise ValueError("Sıfıra bölme hatası!")
    return a / b

def kare(sayi):
    """Sayının karesini alır"""
    return sayi ** 2