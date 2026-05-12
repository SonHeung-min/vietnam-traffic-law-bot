def _roman_to_int(roman: str) -> int:
    """Chuyển số La Mã sang số nguyên. Nếu đã là số thì trả về luôn."""
    if roman.isdigit():
        return int(roman)
    roman = roman.upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    for i, ch in enumerate(roman):
        if i + 1 < len(roman) and values.get(ch, 0) < values.get(roman[i + 1], 0):
            result -= values.get(ch, 0)
        else:
            result += values.get(ch, 0)
    return result
