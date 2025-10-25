"""Main module."""
from itertools import product, combinations

class Himpunan:
    def __init__(self, iterable=None):
        self.elems = set(iterable) if iterable else set()

    def __repr__(self):
        items = []
        for e in sorted(self.elems, key=lambda x: str(x)):
            if isinstance(e, Himpunan):
                items.append(repr(e))
            else:
                items.append(str(e))
        return f"Himpunan({{{', '.join(items)}}})"

    def __len__(self):
        return len(self.elems)

    def __contains__(self, item):
        return item in self.elems

    def __eq__(self, other):
        return isinstance(other, Himpunan) and self.elems == other.elems

    def __hash__(self):
        frozen = tuple(sorted(hash(e) for e in self.elems))
        return hash(frozen)

    def __le__(self, other):
        return self.elems.issubset(other.elems)

    def __lt__(self, other):
        return self.elems < other.elems

    def __ge__(self, other):
        return self.elems.issuperset(other.elems)

    def __floordiv__(self, other):
        return self.elems == other.elems

    def __truediv__(self, other):
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dilakukan antar Himpunan")
        return Himpunan(self.elems & other.elems)

    def __add__(self, other):
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dilakukan antar Himpunan")
        return Himpunan(self.elems | other.elems)

    def __iadd__(self, item):
        self.elems.add(item)
        return self

    def __sub__(self, other):
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dilakukan antar Himpunan")
        return Himpunan(self.elems - other.elems)

    def __mul__(self, other):
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dilakukan antar Himpunan")
        return Himpunan(self.elems ^ other.elems)

    def __pow__(self, other):
        if not isinstance(other, Himpunan):
            raise TypeError("Operasi hanya bisa dilakukan antar Himpunan")
        hasil = set(product(self.elems, other.elems))
        return Himpunan(hasil)

    def komplement(self, semesta):
        return Himpunan(semesta.elems - self.elems)

    def __abs__(self):
        return Himpunan(self.ListKuasa())

    def ListKuasa(self):
        subset_list = []
        elems_list = list(self.elems)
        for i in range(len(elems_list) + 1):
            for combo in combinations(elems_list, i):
                subset_list.append(Himpunan(combo))
        return subset_list
