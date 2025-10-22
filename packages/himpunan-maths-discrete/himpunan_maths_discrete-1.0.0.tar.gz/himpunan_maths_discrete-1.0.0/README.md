# Himpunan - Matematika Diskrit

[![PyPI version](https://badge.fury.io/py/himpunan-maths-discrete.svg)](https://badge.fury.io/py/himpunan-maths-discrete)
[![Python Version](https://img.shields.io/pypi/pyversions/himpunan-maths-discrete.svg)](https://pypi.org/project/himpunan-maths-discrete/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Implementasi teori himpunan (set theory) untuk Matematika Diskrit dalam Python. Package ini dibuat untuk tujuan pembelajaran dan mengimplementasikan berbagai operasi himpunan menggunakan list sebagai struktur data dasar, tanpa menggunakan built-in `set` dari Python.

## Fitur

- ✅ Operasi dasar himpunan (gabungan, irisan, selisih, komplemen)
- ✅ Operasi lanjutan (selisih simetris, cartesian product, himpunan kuasa)
- ✅ Perbandingan himpunan (subset, superset, proper subset)
- ✅ Magic methods Python untuk sintaks yang intuitif
- ✅ Tanpa menggunakan built-in `set` Python
- ✅ Dokumentasi lengkap dalam Bahasa Indonesia

## Instalasi

Install menggunakan pip:

```bash
pip install himpunan-maths-discrete
```

## Penggunaan Dasar

```python
from himpunan_maths_discrete import Himpunan

# Membuat himpunan
h1 = Himpunan(1, 2, 3)
h2 = Himpunan(3, 4, 5)
S = Himpunan(1, 2, 3, 4, 5, 6, 7, 8, 9)

# Kardinalitas (jumlah elemen)
print(len(h1))  # Output: 3

# Keanggotaan
print(3 in h1)  # Output: True
print(6 in h1)  # Output: False

# Menambah elemen
h1 += 4
print(h1)  # Output: {1, 2, 3, 4}
```

## Operasi Himpunan

### 1. Gabungan (Union) - Operator `+`

```python
h1 = Himpunan(1, 2, 3)
h2 = Himpunan(3, 4, 5)
h_gabungan = h1 + h2
print(h_gabungan)  # Output: {1, 2, 3, 4, 5}
```

### 2. Irisan (Intersection) - Operator `/`

```python
h1 = Himpunan(1, 2, 3, 4)
h2 = Himpunan(3, 4, 5)
h_irisan = h1 / h2
print(h_irisan)  # Output: {3, 4}
```

### 3. Selisih (Difference) - Operator `-`

```python
h1 = Himpunan(1, 2, 3, 4)
h2 = Himpunan(3, 4, 5)
h_selisih = h1 - h2
print(h_selisih)  # Output: {1, 2}
```

### 4. Komplemen (Complement)

```python
S = Himpunan(1, 2, 3, 4, 5, 6, 7, 8, 9)
h1 = Himpunan(1, 2, 3)
h_komplemen = h1.Komplemen(S)
print(h_komplemen)  # Output: {4, 5, 6, 7, 8, 9}
```

### 5. Selisih Simetris (Symmetric Difference) - Operator `*`

```python
h1 = Himpunan(1, 2, 3, 4)
h2 = Himpunan(3, 4, 5)
h_simdiff = h1 * h2
print(h_simdiff)  # Output: {1, 2, 5}
```

### 6. Cartesian Product - Operator `**`

```python
h1 = Himpunan(1, 2)
h2 = Himpunan('a', 'b')
h_cartesian = h1 ** h2
print(h_cartesian)  # Output: {(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')}
```

## Perbandingan Himpunan

### Subset dan Superset

```python
h_kecil = Himpunan(1, 2)
h_besar = Himpunan(1, 2, 3, 4, 5)

# Subset (<=)
print(h_kecil <= h_besar)  # Output: True

# Proper Subset (<)
print(h_kecil < h_besar)   # Output: True

# Superset (>=)
print(h_besar >= h_kecil)  # Output: True

# Kesamaan (==)
h1 = Himpunan(1, 2, 3)
h2 = Himpunan(3, 2, 1)
print(h1 == h2)  # Output: True

# Ekuivalensi (//)
print(h1 // h2)  # Output: True
```

## Himpunan Kuasa (Power Set)

```python
h = Himpunan(1, 2, 3)

# Jumlah anggota himpunan kuasa
print(abs(h))  # Output: 8 (karena 2^3 = 8)

# List semua subset
power_set = h.ListKuasa()
for subset in power_set:
    print(subset)
# Output:
# {}
# {1}
# {2}
# {1, 2}
# {3}
# {1, 3}
# {2, 3}
# {1, 2, 3}
```

## Referensi Magic Methods

| Operasi           | Magic Method   | Operator/Fungsi | Deskripsi                            |
| ----------------- | -------------- | --------------- | ------------------------------------ |
| Kardinalitas      | `__len__`      | `len()`         | Jumlah elemen dalam himpunan         |
| Keanggotaan       | `__contains__` | `in`            | Cek apakah elemen ada dalam himpunan |
| Kesamaan          | `__eq__`       | `==`            | Cek apakah dua himpunan sama         |
| Subset            | `__le__`       | `<=`            | Cek apakah subset                    |
| Proper Subset     | `__lt__`       | `<`             | Cek apakah proper subset             |
| Superset          | `__ge__`       | `>=`            | Cek apakah superset                  |
| Ekuivalensi       | `__floordiv__` | `//`            | Cek ekuivalensi                      |
| Irisan            | `__truediv__`  | `/`             | Irisan dua himpunan                  |
| Gabungan          | `__add__`      | `+`             | Gabungan dua himpunan                |
| Selisih           | `__sub__`      | `-`             | Selisih dua himpunan                 |
| Selisih Simetris  | `__mul__`      | `*`             | Selisih simetris                     |
| Cartesian Product | `__pow__`      | `**`            | Cartesian product                    |
| Jumlah Subset     | `__abs__`      | `abs()`         | Jumlah anggota power set             |
| Tambah Elemen     | `__iadd__`     | `+=`            | Menambah elemen                      |
| Kurang Elemen     | `__isub__`     | `-=`            | Mengurangi elemen                    |

## Metode Tambahan

- `tambah(item)` - Menambah elemen ke himpunan
- `kurang(item)` - Mengurangi elemen dari himpunan
- `Komplemen(semesta)` - Menghitung komplemen terhadap himpunan semesta
- `ListKuasa()` - Mengembalikan list semua subset

## Contoh Lengkap

```python
from himpunan_maths_discrete import Himpunan

# Definisi himpunan semesta dan subset
S = Himpunan(1, 2, 3, 4, 5, 6, 7, 8, 9)
h1 = Himpunan(1, 2, 3)
h2 = Himpunan(3, 4, 5)

# Operasi dasar
print(f"h1 = {h1}")
print(f"h2 = {h2}")
print(f"h1 + h2 = {h1 + h2}")  # Gabungan
print(f"h1 / h2 = {h1 / h2}")  # Irisan
print(f"h1 - h2 = {h1 - h2}")  # Selisih
print(f"h1 * h2 = {h1 * h2}")  # Selisih Simetris

# Komplemen
print(f"h1' = {h1.Komplemen(S)}")

# Himpunan Kuasa
h_kecil = Himpunan(1, 2)
print(f"Power set dari {h_kecil}:")
for subset in h_kecil.ListKuasa():
    print(f"  {subset}")
```

## Requirements

- Python >= 3.7
- Tidak ada dependencies eksternal

## Lisensi

MIT License - Lihat file [LICENSE](LICENSE) untuk detail lebih lanjut.

## Kontribusi

Kontribusi sangat diterima! Silakan buat issue atau pull request di repository GitHub.

## Author

Wyatt Matthew - [wyatt.honny06@gmail.com](mailto:wyatt.honny06@gmail.com)

## Acknowledgments

Package ini dibuat sebagai bagian dari tugas Matematika Diskrit untuk implementasi teori himpunan dalam pemrograman Python.

---

**Catatan**: Package ini dibuat untuk tujuan pembelajaran dan tidak menggunakan built-in `set` dari Python sesuai dengan requirements tugas.
