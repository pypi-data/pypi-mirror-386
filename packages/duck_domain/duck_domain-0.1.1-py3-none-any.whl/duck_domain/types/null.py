class _TypeNull:
    __slots__ = ()

    def __repr__(self) -> str:
        return "Null"

    def __str__(self) -> str:
        return "null"

Null = _TypeNull()

