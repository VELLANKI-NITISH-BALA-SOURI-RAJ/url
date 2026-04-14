from app.core.config import settings

def encode_base62(num: int) -> str:
    """Encodes a positive integer into a base62 string."""
    if num == 0:
        return settings.BASE62_ALPHABET[0]
    
    arr = []
    base = len(settings.BASE62_ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(settings.BASE62_ALPHABET[rem])
    
    arr.reverse()
    return ''.join(arr)

def decode_base62(string: str) -> int:
    """Decodes a base62 string back into an integer."""
    base = len(settings.BASE62_ALPHABET)
    strlen = len(string)
    num = 0
    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += settings.BASE62_ALPHABET.index(char) * (base ** power)
        idx += 1
    return num
