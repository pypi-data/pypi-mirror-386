"""
Himpunan - A Python implementation of Set Theory operations
Implementasi konsep teori himpunan untuk Matematika Diskrit
"""


class Himpunan:
    """
    Kelas untuk merepresentasikan himpunan (set) dalam matematika diskrit.
    Menggunakan list sebagai struktur data dasar tanpa menggunakan built-in set.
    
    Attributes:
        _elements (list): List yang menyimpan elemen-elemen himpunan (tanpa duplikasi)
    """
    
    def __init__(self, *elements):
        """
        Inisialisasi himpunan dengan elemen-elemen yang diberikan.
        Otomatis menghilangkan duplikasi.
        
        Args:
            *elements: Elemen-elemen yang akan dimasukkan ke himpunan
        
        Example:
            h = Himpunan(1, 2, 3, 2, 1)  # Akan menjadi {1, 2, 3}
        """
        self._elements = []
        for element in elements:
            if element not in self._elements:
                self._elements.append(element)
    
    def tambah(self, item):
        """
        Menambah satu elemen ke himpunan.
        Tidak menambahkan jika elemen sudah ada.
        
        Args:
            item: Elemen yang akan ditambahkan
        """
        if item not in self._elements:
            self._elements.append(item)
    
    def kurang(self, item):
        """
        Mengurangi/menghapus satu elemen dari himpunan.
        
        Args:
            item: Elemen yang akan dihapus
        
        Raises:
            ValueError: Jika elemen tidak ada dalam himpunan
        """
        if item in self._elements:
            self._elements.remove(item)
        else:
            raise ValueError(f"Elemen {item} tidak ada dalam himpunan")
    
    def __len__(self):
        """
        Mengembalikan jumlah elemen dalam himpunan (kardinalitas).
        
        Returns:
            int: Jumlah elemen dalam himpunan
        
        Example:
            h = Himpunan(1, 2, 3)
            len(h)  # Output: 3
        """
        return len(self._elements)
    
    def __contains__(self, item):
        """
        Mengecek apakah suatu elemen ada dalam himpunan.
        Digunakan dengan operator 'in'.
        
        Args:
            item: Elemen yang dicek
        
        Returns:
            bool: True jika elemen ada, False jika tidak
        
        Example:
            h = Himpunan(1, 2, 3)
            3 in h  # Output: True
            5 in h  # Output: False
        """
        return item in self._elements
    
    def __eq__(self, other):
        """
        Mengecek apakah dua himpunan sama (memiliki elemen yang sama).
        Digunakan dengan operator ==.
        
        Args:
            other (Himpunan): Himpunan yang akan dibandingkan
        
        Returns:
            bool: True jika kedua himpunan sama, False jika tidak
        
        Example:
            h1 = Himpunan(1, 2, 3)
            h2 = Himpunan(3, 2, 1)
            h1 == h2  # Output: True
        """
        if not isinstance(other, Himpunan):
            return False
        if len(self) != len(other):
            return False
        for element in self._elements:
            if element not in other._elements:
                return False
        return True
    
    def __le__(self, other):
        """
        Mengecek apakah himpunan ini adalah subset dari himpunan lain.
        A ⊆ B: Semua elemen A ada di B.
        Digunakan dengan operator <=.
        
        Args:
            other (Himpunan): Himpunan yang akan dibandingkan
        
        Returns:
            bool: True jika self adalah subset dari other
        
        Example:
            h1 = Himpunan(1, 2)
            h2 = Himpunan(1, 2, 3)
            h1 <= h2  # Output: True
        """
        if not isinstance(other, Himpunan):
            return False
        for element in self._elements:
            if element not in other._elements:
                return False
        return True
    
    def __lt__(self, other):
        """
        Mengecek apakah himpunan ini adalah proper subset dari himpunan lain.
        A ⊂ B: A adalah subset dari B dan A ≠ B.
        Digunakan dengan operator <.
        
        Args:
            other (Himpunan): Himpunan yang akan dibandingkan
        
        Returns:
            bool: True jika self adalah proper subset dari other
        
        Example:
            h1 = Himpunan(1, 2)
            h2 = Himpunan(1, 2, 3)
            h1 < h2  # Output: True
        """
        return self <= other and self != other
    
    def __ge__(self, other):
        """
        Mengecek apakah himpunan ini adalah superset dari himpunan lain.
        A ⊇ B: Semua elemen B ada di A.
        Digunakan dengan operator >=.
        
        Args:
            other (Himpunan): Himpunan yang akan dibandingkan
        
        Returns:
            bool: True jika self adalah superset dari other
        
        Example:
            h1 = Himpunan(1, 2, 3)
            h2 = Himpunan(1, 2)
            h1 >= h2  # Output: True
        """
        if not isinstance(other, Himpunan):
            return False
        return other <= self
    
    def __floordiv__(self, other):
        """
        Mengecek apakah dua himpunan ekuivalen (sama persis).
        Sama dengan operator ==, untuk memenuhi requirement assignment.
        Digunakan dengan operator //.
        
        Args:
            other (Himpunan): Himpunan yang akan dibandingkan
        
        Returns:
            bool: True jika kedua himpunan ekuivalen
        
        Example:
            h1 = Himpunan(1, 2, 3)
            h2 = Himpunan(3, 2, 1)
            h1 // h2  # Output: True
        """
        return self == other
    
    def __truediv__(self, other):
        """
        Menghitung irisan (intersection) antara dua himpunan.
        A ∩ B: Elemen yang ada di A dan B.
        Digunakan dengan operator /.
        
        Args:
            other (Himpunan): Himpunan yang akan di-irisan
        
        Returns:
            Himpunan: Himpunan hasil irisan
        
        Example:
            h1 = Himpunan(1, 2, 3)
            h2 = Himpunan(3, 4, 5)
            h3 = h1 / h2  # Output: Himpunan(3)
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi irisan hanya bisa dilakukan dengan Himpunan")
        result = Himpunan()
        for element in self._elements:
            if element in other._elements:
                result.tambah(element)
        return result
    
    def __add__(self, other):
        """
        Menghitung gabungan (union) antara dua himpunan.
        A ∪ B: Semua elemen yang ada di A atau B.
        Digunakan dengan operator +.
        
        Args:
            other (Himpunan): Himpunan yang akan digabung
        
        Returns:
            Himpunan: Himpunan hasil gabungan
        
        Example:
            h1 = Himpunan(1, 2, 3)
            h2 = Himpunan(3, 4, 5)
            h3 = h1 + h2  # Output: Himpunan(1, 2, 3, 4, 5)
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi gabungan hanya bisa dilakukan dengan Himpunan")
        result = Himpunan(*self._elements)
        for element in other._elements:
            result.tambah(element)
        return result
    
    def __sub__(self, other):
        """
        Menghitung selisih (difference) antara dua himpunan.
        A - B: Elemen yang ada di A tapi tidak di B.
        Digunakan dengan operator -.
        
        Args:
            other (Himpunan): Himpunan yang akan dikurangkan
        
        Returns:
            Himpunan: Himpunan hasil selisih
        
        Example:
            h1 = Himpunan(1, 2, 3, 4)
            h2 = Himpunan(3, 4, 5)
            h3 = h1 - h2  # Output: Himpunan(1, 2)
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi selisih hanya bisa dilakukan dengan Himpunan")
        result = Himpunan()
        for element in self._elements:
            if element not in other._elements:
                result.tambah(element)
        return result
    
    def Komplemen(self, semesta):
        """
        Menghitung komplemen dari himpunan terhadap himpunan semesta.
        A': Elemen yang ada di semesta tapi tidak di A.
        
        Args:
            semesta (Himpunan): Himpunan semesta
        
        Returns:
            Himpunan: Himpunan komplemen
        
        Example:
            S = Himpunan(1, 2, 3, 4, 5)
            h1 = Himpunan(1, 2, 3)
            h2 = h1.Komplemen(S)  # Output: Himpunan(4, 5)
        """
        if not isinstance(semesta, Himpunan):
            raise TypeError("Semesta harus berupa Himpunan")
        return semesta - self
    
    def __mul__(self, other):
        """
        Menghitung selisih simetris (symmetric difference) antara dua himpunan.
        A △ B: Elemen yang ada di A atau B, tapi tidak di keduanya.
        Sama dengan (A - B) ∪ (B - A) atau (A ∪ B) - (A ∩ B).
        Digunakan dengan operator *.
        
        Args:
            other (Himpunan): Himpunan yang akan dihitung selisih simetrisnya
        
        Returns:
            Himpunan: Himpunan hasil selisih simetris
        
        Example:
            h1 = Himpunan(1, 2, 3)
            h2 = Himpunan(3, 4, 5)
            h3 = h1 * h2  # Output: Himpunan(1, 2, 4, 5)
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi selisih simetris hanya bisa dilakukan dengan Himpunan")
        return (self - other) + (other - self)
    
    def __pow__(self, other):
        """
        Menghitung cartesian product dari dua himpunan.
        A × B: Himpunan semua pasangan terurut (a, b) dengan a ∈ A dan b ∈ B.
        Digunakan dengan operator **.
        
        Args:
            other (Himpunan): Himpunan yang akan dikalikan secara kartesian
        
        Returns:
            Himpunan: Himpunan berisi tuple pasangan terurut
        
        Example:
            h1 = Himpunan(1, 2)
            h2 = Himpunan('a', 'b')
            h3 = h1 ** h2  # Output: Himpunan((1,'a'), (1,'b'), (2,'a'), (2,'b'))
        """
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi cartesian product hanya bisa dilakukan dengan Himpunan")
        result = Himpunan()
        for elem1 in self._elements:
            for elem2 in other._elements:
                result.tambah((elem1, elem2))
        return result
    
    def __abs__(self):
        """
        Menghitung jumlah anggota himpunan kuasa (power set).
        Jumlah subset dari himpunan dengan n elemen adalah 2^n.
        Digunakan dengan fungsi abs().
        
        Returns:
            int: Jumlah anggota himpunan kuasa (2^n)
        
        Example:
            h = Himpunan(1, 2, 3)
            abs(h)  # Output: 8 (karena 2^3 = 8)
        """
        return 2 ** len(self)
    
    def ListKuasa(self):
        """
        Menampilkan list semua subset dari himpunan (himpunan kuasa / power set).
        P(A): Himpunan dari semua subset dari A.
        
        Returns:
            list: List berisi semua subset (dalam bentuk Himpunan)
        
        Example:
            h = Himpunan(1, 2)
            h.ListKuasa()  # Output: [Himpunan(), Himpunan(1), Himpunan(2), Himpunan(1,2)]
        """
        power_set = []
        n = len(self)
        
        # Generate semua kombinasi menggunakan bitmask
        # Untuk n elemen, ada 2^n subset
        for i in range(2 ** n):
            subset = Himpunan()
            for j in range(n):
                # Cek apakah bit ke-j dari i adalah 1
                if i & (1 << j):
                    subset.tambah(self._elements[j])
            power_set.append(subset)
        
        return power_set
    
    def __iadd__(self, item):
        """
        Menambah elemen ke himpunan menggunakan operator +=.
        
        Args:
            item: Elemen yang akan ditambahkan
        
        Returns:
            Himpunan: Himpunan yang sudah ditambah (self)
        
        Example:
            h = Himpunan(1, 2, 3)
            h += 4  # h menjadi Himpunan(1, 2, 3, 4)
        """
        self.tambah(item)
        return self
    
    def __isub__(self, item):
        """
        Mengurangi elemen dari himpunan menggunakan operator -=.
        
        Args:
            item: Elemen yang akan dihapus
        
        Returns:
            Himpunan: Himpunan yang sudah dikurangi (self)
        
        Example:
            h = Himpunan(1, 2, 3)
            h -= 2  # h menjadi Himpunan(1, 3)
        """
        self.kurang(item)
        return self
    
    def __str__(self):
        """
        Representasi string dari himpunan untuk print().
        
        Returns:
            str: String representasi himpunan dalam format {elem1, elem2, ...}
        """
        if len(self._elements) == 0:
            return "{}"
        return "{" + ", ".join(str(elem) for elem in self._elements) + "}"
    
    def __repr__(self):
        """
        Representasi resmi dari himpunan untuk debugging.
        
        Returns:
            str: String representasi dalam format Himpunan(elem1, elem2, ...)
        """
        if len(self._elements) == 0:
            return "Himpunan()"
        return "Himpunan(" + ", ".join(repr(elem) for elem in self._elements) + ")"
