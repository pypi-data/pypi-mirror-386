# -*- coding: utf-8 -*-
"""
Basit Türkçe -> Python çeviri iskeleti.

Not: Bu çevirici bağlamdan bağımsız basit anahtar kelime eşleştirmeleri yapar.
İçerik dizgilerinde (string) geçen sözcükleri ayırt etmez; gelişmiş kullanım
için bir söz dizimi ayrıştırıcı gerekir. Burada amaç, temel bir çalışma örneği
sağlamaktır.
"""
from typing import Dict, Tuple, Optional
import re

# Basit eşlemeler (ihtiyaca göre genişletilebilir)
_TOKENS: Dict[str, str] = {
    # Mantık değerleri ve operatörleri
    "doğru": "True",
    "yanlış": "False",
    "ve": "and",
    "veya": "or",
    "değil": "not",
    # Sık kullanılan fonksiyon adları
    "yaz": "print",
    "al": "input",
}


def _basit_degistir(kod: str, eşlemeler: Dict[str, str]) -> str:
    """Kelime sınırı bazlı basit değiştirme.

    Uyarı: Stringler ve yorumlar içinde de değiştirme yapabilir.
    """
    if not eşlemeler:
        return kod
    desen = r"\b(" + "|".join(map(re.escape, eşlemeler.keys())) + r")\b"

    def _repl(eşleşme: re.Match) -> str:
        sözcük = eşleşme.group(1)
        return eşlemeler.get(sözcük, sözcük)

    return re.sub(desen, _repl, kod)


def kod_cevir(kod: str) -> str:
    """Türkçe benzeri kodu Python koduna basitçe dönüştürür."""
    return _basit_degistir(kod, _TOKENS)


def çalıştır_türkçe(kod: str,
                    globalns: Optional[dict] = None,
                    localns: Optional[dict] = None) -> Tuple[dict, dict]:
    """Verilen Türkçe benzeri kodu dönüştürüp çalıştırır ve kullanılan ad alanlarını döndürür."""
    py_kod = kod_cevir(kod)
    g = {} if globalns is None else globalns
    l = g if localns is None else localns
    exec(py_kod, g, l)
    return g, l
