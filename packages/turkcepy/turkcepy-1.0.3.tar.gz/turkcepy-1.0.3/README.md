
# TürkçePy

Türkçe anahtar kelimelerle Python programlama yapmanızı sağlayan bir kütüphane.

## Kurulum

```bash
pip install turkcepy
```

## Kullanım

Kısa takma ad ile:

```python
import tr

tr.yaz("Merhaba Dünya")
print(tr.liste(1, 2, 3))
print(tr.mat_topla(5, 7))
```

Doğrudan paket ile:

```python
from turkcepy import yaz, liste, mat_topla

yaz("Merhaba")
print(liste(range(3)))
print(mat_topla(2, 3))
```

Basit çevirici:

```python
from turkcepy import kod_cevir, çalıştır_türkçe

py_kod = kod_cevir("yaz('selam')")
print(py_kod)  # print('selam')

çalıştır_türkçe("yaz('selam')")
```
