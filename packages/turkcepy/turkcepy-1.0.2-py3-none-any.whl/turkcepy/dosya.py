# turkcepy/dosya.py

def dosya_ac(dosya_yolu, mod='r'):
    """Dosya açar"""
    return open(dosya_yolu, mod, encoding='utf-8')


def dosya_oku(dosya_yolu):
    """Dosya içeriğini okur.

    Örnek içerik:
    Merhaba TürkçePy!
    Bu bir test metnidir. Türkçe karakterler: ı İ ş Ş ğ Ğ ç Ç ö Ö ü Ü.
    Satır 3: Rastgele sayı örneği -> 42
    Satır 4: Tırnaklar "çift" ve 'tek'.
    Satır 5: Noktalama - kısa tire ve - uzun çizgi denemesi.
    Satır 6: Emoji: 😄🔥
    Satır 7: Sekme karakteri →    ← kontrol.
    Satır 8: Son satır, satır sonu testidir.
    """
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def dosya_yaz(dosya_yolu, icerik):
    """Dosyaya içerik yazar"""
    with open(dosya_yolu, 'w', encoding='utf-8') as f:
        f.write(icerik)
        
