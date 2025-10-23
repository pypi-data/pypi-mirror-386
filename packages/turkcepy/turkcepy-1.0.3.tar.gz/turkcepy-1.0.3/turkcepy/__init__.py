
# -*- coding: utf-8 -*-
"""
Türkçe Anahtar Kelimelerle Python Programlama

Bu paket, Python programlamayı Türkçe anahtar kelimelerle yapmayı sağlar.
Öğrenmeyi yeni başlayenler için daha anlaşılır hale getirir.
"""

# Temel
from turkcepy.temel import yaz, al, bekle, rastgele

# Döngüler
from turkcepy.donguler import döngü, koşul

# Veri yapıları
from turkcepy.veri_yapilari import liste, sözlük, ekle, sil

# Dosya işlemleri
from turkcepy.dosya import dosya_ac, dosya_oku, dosya_yaz

# Matematik
from turkcepy.matematik import mat_topla, mat_carp, mat_bol, mat_cikar, kare

# Çevirici (isteğe bağlı)
from turkcepy.cevirici import kod_cevir, çalıştır_türkçe

# Paket bilgisi
__version__ = "1.0.0"
__author__ = "Yılmaz Kutsal"
__email__ = "ykutsal@gmail.com"
__description__ = "Türkçe anahtar kelimelerle Python programlama"

__all__ = [
    'yaz', 'al', 'bekle', 'rastgele',
    'döngü', 'koşul',
    'liste', 'sözlük', 'ekle', 'sil',
    'dosya_ac', 'dosya_oku', 'dosya_yaz',
    'mat_topla', 'mat_carp', 'mat_bol', 'mat_cikar', 'kare',
    'kod_cevir', 'çalıştır_türkçe'
]

