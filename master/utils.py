BASE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def to_base(s, b):
    res = ""
    while s:
        res += BASE[s % b]
        s //= b
    return res[::-1] or "0"
