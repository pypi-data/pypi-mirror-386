# -*- coding: utf-8 -*-
"""
Döngü ve koşul yardımcıları
"""
from typing import Iterable, Callable, Any, Optional


def döngü(dizi: Iterable, işlem: Callable[[Any], Any]) -> None:
    """Verilen iterable üzerinde dolaşır ve her öge için işlem fonksiyonunu çağırır.

    Örnek:
        döngü([1, 2, 3], lambda x: print(x))
    """
    for öge in dizi:
        işlem(öge)


def koşul(şart: bool,
         doğru: Optional[Callable[[], Any]] = None,
         yanlış: Optional[Callable[[], Any]] = None) -> Any:
    """Basit bir koşul yardımcı fonksiyonu.

    - şart True ise 'doğru' çağrılır ve sonucu döner (verildiyse), aksi halde True döner.
    - şart False ise 'yanlış' çağrılır ve sonucu döner (verildiyse), aksi halde False döner.

    Örnek:
        koşul(x > 0, doğru=lambda: print("pozitif"), yanlış=lambda: print("negatif veya sıfır"))
    """
    if şart:
        return doğru() if callable(doğru) else True
    else:
        return yanlış() if callable(yanlış) else False
