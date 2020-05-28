"""A module allowing to generate and translate numeric identifiers from the `FoodEx2`_
*term code* strings. A *term code* consists of a string of five alphanumeric characters,
e.g. :const:`'A111J'`. While most of the times they start with an :const:`A` character,
this module does not restrict to that.

"""
BASE = 36
ASCII_SHIFT = 64


def _char_to_dec(character: str) -> int:
    c = character.upper()

    if (ord(c) < 48 or ord(c) > 57) and (ord(c) < 65 or ord(c) > 90):
        raise ValueError(
            "expected an alphanumeric character ([0-9], [A-Z], [a-z]), got "
            f"'{character}' instead"
        )

    if character.isdigit():
        return int(c)
    else:
        return ord(c) - ASCII_SHIFT + 9


def _to_ascii(number: int) -> str:
    if number < 0 or number > 35:
        raise ValueError(
            f"expected an integer in the range (0, 35), got '{number}' instead"
        )

    if number < 10:
        return str(number)
    else:
        return chr(number - 9 + ASCII_SHIFT)


def to_int(code: str) -> int:
    """Function generating a numeric identifier from a FoodEx2 *term code*.

    :param str code: FoodEx2 *term code*
    :return: A numeric translation of the *term code*
    :rtype: int
    """
    r = 0
    index = 4

    for c in code:
        r += _char_to_dec(c) * (BASE ** index)
        index -= 1

    return r


def to_str(code: int) -> str:
    """Function generating a FoodEx2 *term code* from its numeric representation.

    :param int code: A numeric identifier
    :return: A string translation in the form of a FoodEx2 *term code*
    :rtype: str
    """
    s = ""

    for n in range(4, -1, -1):
        s += _to_ascii(code // (BASE ** n))
        code = code % (BASE ** n)

    return s
