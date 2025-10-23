# -*- coding: utf-8 -*-
"""
Temel veri yapıları ve yardımcı işlemler
"""
from collections.abc import Iterable as _Iterable
from typing import Any, Dict


def liste(*öğeler) -> list:
    """Liste oluşturur.

    Kullanım:
        - liste(1, 2, 3) => [1, 2, 3]
        - liste([1, 2, 3]) => [1, 2, 3]
        - liste(range(3)) => [0, 1, 2]
    """
    if len(öğeler) == 1 and isinstance(öğeler[0], _Iterable) and not isinstance(öğeler[0], (str, bytes, bytearray)):
        return list(öğeler[0])
    return list(öğeler)


def sözlük(*args, **kwargs) -> Dict[str, Any]:
    """Sözlük (dict) oluşturur.

    Kullanım:
        - sözlük(a=1, b=2)
        - sözlük({"a": 1}, b=2)
        - sözlük([("a", 1), ("b", 2)])
    """
    d: Dict[str, Any] = {}
    for arg in args:
        if isinstance(arg, dict):
            d.update(arg)
        else:
            d.update(dict(arg))
    d.update(kwargs)
    return d


def ekle(koleksiyon, öğe, değer=None):
    """Koleksiyona öğe ekler.

    - liste: append
    - küme: add
    - sözlük: koleksiyon[öğe] = değer (değer verilmelidir)
    """
    if isinstance(koleksiyon, list):
        koleksiyon.append(öğe)
    elif isinstance(koleksiyon, set):
        koleksiyon.add(öğe)
    elif isinstance(koleksiyon, dict):
        if değer is None:
            raise ValueError("Sözlük için 'değer' belirtmelisiniz.")
        koleksiyon[öğe] = değer
    else:
        raise TypeError("Desteklenmeyen koleksiyon tipi: {}".format(type(koleksiyon).__name__))
    return koleksiyon


def sil(koleksiyon, öğe=None):
    """Koleksiyondan öğe siler.

    - liste: öğe verilirse remove, verilmezse pop (son eleman)
    - küme: öğe verilmelidir, discard ile silinir
    - sözlük: öğe (anahtar) verilirse pop, verilmezse clear
    """
    if isinstance(koleksiyon, list):
        if öğe is None:
            return koleksiyon.pop()
        koleksiyon.remove(öğe)
        return koleksiyon
    elif isinstance(koleksiyon, set):
        if öğe is None:
            raise ValueError("Kümeler için silinecek öğe belirtilmelidir.")
        koleksiyon.discard(öğe)
        return koleksiyon
    elif isinstance(koleksiyon, dict):
        if öğe is None:
            koleksiyon.clear()
            return koleksiyon
        koleksiyon.pop(öğe, None)
        return koleksiyon
    else:
        raise TypeError("Desteklenmeyen koleksiyon tipi: {}".format(type(koleksiyon).__name__))
