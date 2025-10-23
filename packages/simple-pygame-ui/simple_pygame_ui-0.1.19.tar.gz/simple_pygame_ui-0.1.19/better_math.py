


class Vector2i:

    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        if isinstance(other, Vector2i):
            return Vector2i(self.x + other.x, self.y + other.y)
        return Vector2i(self.x + other, self.y + other)

    def __mul__(self, other):
        if isinstance(other, Vector2i):
            return Vector2i(self.x * other.x, self.y * other.y)
        return Vector2i(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector2i):
            return Vector2i(self.x // other.x, self.y // other.y)  # int-Division
        return Vector2i(self.x // other, self.y // other)

    def __abs__(self):
        return Vector2i(abs(self.x), abs(self.y))

    def __neg__(self):
        return Vector2i(-self.x, -self.y)

    def __pow__(self, power, modulo=None):
        if modulo is None:
            return Vector2i(self.x ** power, self.y ** power)
        return Vector2i(pow(self.x, power, modulo), pow(self.y, power, modulo))

    def __repr__(self):
        return f"Vector2i({self.x}, {self.y})"
    def __str__(self):
        return f"({self.x}, {self.y})"
