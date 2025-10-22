# himpunanmatdis

Implementasi konsep **Himpunan (Set)** untuk mata kuliah **Matematika Diskrit** tanpa menggunakan `set()` bawaan Python.

Fitur
- Gabungan (+)
- Irisan (/)
- Selisih (-)
- Selisih Simetris (*)
- Ekuivalensi (//)
- Subset, Proper Subset, Superset
- Komplemen
- Himpunan Kuasa (abs)
- Produk Kartesius (**)


Contoh Penggunaan
```python
from himpunanmatdis.himpunan import Himpunan

S = Himpunan(1,2,3,4,5,6,7,8,9)
h1 = Himpunan(1, 2, 3)
h2 = Himpunan(3, 4, 5)

print(len(h1))      # 3
print(3 in h1)      # True
print(h1 == h2)     # False

h3 = h1 / h2        # Irisan
print(h3)           # {3}

h4 = h1 + h2        # Gabungan
print(h4)           # {1, 2, 3, 4, 5}

h5 = h1 - h2        # Selisih
print(h5)           # {1, 2}

print(abs(h1))      # Himpunan Kuasa

