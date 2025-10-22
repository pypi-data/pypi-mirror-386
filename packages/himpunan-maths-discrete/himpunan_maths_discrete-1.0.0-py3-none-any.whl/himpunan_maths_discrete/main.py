"""
Contoh penggunaan kelas Himpunan
Demonstrasi semua operasi himpunan yang tersedia
"""

from .himpunan import Himpunan


def main():
    """Fungsi utama untuk mendemonstrasikan penggunaan kelas Himpunan"""
    
    print("=" * 60)
    print("DEMONSTRASI KELAS HIMPUNAN - MATEMATIKA DISKRIT")
    print("=" * 60)
    
    # Membuat himpunan
    print("\n1. MEMBUAT HIMPUNAN")
    print("-" * 60)
    S = Himpunan(1, 2, 3, 4, 5, 6, 7, 8, 9)
    h1 = Himpunan(1, 2, 3)
    h2 = Himpunan(3, 4, 5)
    print(f"S (Semesta) = {S}")
    print(f"h1 = {h1}")
    print(f"h2 = {h2}")
    
    # Magic method __len__
    print("\n2. KARDINALITAS (__len__)")
    print("-" * 60)
    print(f"len(h1) = {len(h1)}")  # Output: 3
    print(f"len(h2) = {len(h2)}")  # Output: 3
    
    # Magic method __contains__
    print("\n3. KEANGGOTAAN (__contains__)")
    print("-" * 60)
    print(f"3 in h1 = {3 in h1}")  # Output: True
    print(f"5 in h1 = {5 in h1}")  # Output: False
    
    # Magic method __eq__
    print("\n4. KESAMAAN HIMPUNAN (__eq__)")
    print("-" * 60)
    h3 = Himpunan(3, 2, 1)
    print(f"h3 = {h3}")
    print(f"h1 == h2 = {h1 == h2}")  # Output: False
    print(f"h1 == h3 = {h1 == h3}")  # Output: True
    
    # Menambah elemen dengan +=
    print("\n5. MENAMBAH ELEMEN (+=)")
    print("-" * 60)
    h1_copy = Himpunan(1, 2, 3)
    print(f"h1_copy sebelum = {h1_copy}")
    h1_copy += 4
    print(f"h1_copy setelah += 4 = {h1_copy}")  # Output: {1, 2, 3, 4}
    
    # Update h1 untuk contoh selanjutnya
    h1 = Himpunan(1, 2, 3, 4)
    print(f"\nUpdate h1 = {h1}")
    
    # Irisan (Intersection)
    print("\n6. IRISAN / INTERSECTION (operator /)")
    print("-" * 60)
    h_irisan = h1 / h2
    print(f"h1 / h2 = {h_irisan}")  # Output: {3, 4}
    
    # Gabungan (Union)
    print("\n7. GABUNGAN / UNION (operator +)")
    print("-" * 60)
    h_gabungan = h1 + h2
    print(f"h1 + h2 = {h_gabungan}")  # Output: {1, 2, 3, 4, 5}
    
    # Selisih (Difference)
    print("\n8. SELISIH / DIFFERENCE (operator -)")
    print("-" * 60)
    h_selisih = h1 - h2
    print(f"h1 - h2 = {h_selisih}")  # Output: {1, 2}
    
    # Komplemen
    print("\n9. KOMPLEMEN (method Komplemen)")
    print("-" * 60)
    h_komplemen = h1.Komplemen(S)
    print(f"h1.Komplemen(S) = {h_komplemen}")  # Output: {5, 6, 7, 8, 9}
    
    # Subset dan Superset
    print("\n10. SUBSET DAN SUPERSET (__le__, __lt__, __ge__)")
    print("-" * 60)
    h_kecil = Himpunan(1, 2)
    h_besar = Himpunan(1, 2, 3, 4, 5)
    print(f"h_kecil = {h_kecil}")
    print(f"h_besar = {h_besar}")
    print(f"h_kecil <= h_besar (subset) = {h_kecil <= h_besar}")  # True
    print(f"h_kecil < h_besar (proper subset) = {h_kecil < h_besar}")  # True
    print(f"h_besar >= h_kecil (superset) = {h_besar >= h_kecil}")  # True
    
    # Ekuivalensi
    print("\n11. EKUIVALENSI (__floordiv__)")
    print("-" * 60)
    h_ekuiv1 = Himpunan(1, 2, 3)
    h_ekuiv2 = Himpunan(3, 2, 1)
    print(f"h_ekuiv1 = {h_ekuiv1}")
    print(f"h_ekuiv2 = {h_ekuiv2}")
    print(f"h_ekuiv1 // h_ekuiv2 = {h_ekuiv1 // h_ekuiv2}")  # True
    
    # Selisih Simetris
    print("\n12. SELISIH SIMETRIS / SYMMETRIC DIFFERENCE (operator *)")
    print("-" * 60)
    h_simdiff = h1 * h2
    print(f"h1 * h2 = {h_simdiff}")  # Output: {1, 2, 5}
    
    # Cartesian Product
    print("\n13. CARTESIAN PRODUCT (operator **)")
    print("-" * 60)
    h_cart1 = Himpunan(1, 2)
    h_cart2 = Himpunan('a', 'b')
    h_cartesian = h_cart1 ** h_cart2
    print(f"h_cart1 = {h_cart1}")
    print(f"h_cart2 = {h_cart2}")
    print(f"h_cart1 ** h_cart2 = {h_cartesian}")
    
    # Himpunan Kuasa (Power Set) - jumlah anggota
    print("\n14. JUMLAH ANGGOTA HIMPUNAN KUASA (abs)")
    print("-" * 60)
    h_kuasa_test = Himpunan(1, 2, 3)
    print(f"h_kuasa_test = {h_kuasa_test}")
    print(f"abs(h_kuasa_test) = {abs(h_kuasa_test)}")  # Output: 8 (2^3)
    
    # List Himpunan Kuasa
    print("\n15. LIST HIMPUNAN KUASA (method ListKuasa)")
    print("-" * 60)
    h_kuasa = Himpunan(1, 2)
    power_set = h_kuasa.ListKuasa()
    print(f"h_kuasa = {h_kuasa}")
    print(f"h_kuasa.ListKuasa() = ")
    for i, subset in enumerate(power_set):
        print(f"  {i+1}. {subset}")
    
    # Mengurangi elemen
    print("\n16. MENGURANGI ELEMEN (-=)")
    print("-" * 60)
    h_kurang = Himpunan(1, 2, 3, 4, 5)
    print(f"h_kurang sebelum = {h_kurang}")
    h_kurang -= 3
    print(f"h_kurang setelah -= 3 = {h_kurang}")
    
    print("\n" + "=" * 60)
    print("DEMONSTRASI SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    main()
