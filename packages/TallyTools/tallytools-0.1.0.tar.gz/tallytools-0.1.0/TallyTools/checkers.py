from .to_int import to_int

__all__ = ["type_of", "is_tally"]

def validate_tally(tally_str: str) -> bool:
    if not isinstance(tally_str, str):
        return False

    s = tally_str.strip().upper()
    if not s:
        return False

    if s.startswith("-"):
        s = s[1:].strip()
        if not s:
            return False

    TALLY_STYLES = {"||||/", "|||||", "IIIII"}
    ALLOWED_SINGLE = {"|", "I"}
    BRACKETS = [
        ("(", ")"), ("[", "]"), ("{", "}"), ("<", ">"),
        ("×(", ")"), ("×[", "]"), ("×{", "}"), ("×<", ">"),
        ("*(", ")"), ("*[", "]"), ("*{", "}"), ("*<", ">")
    ]

    i = 0
    n = len(s)

    while i < n:
        if s[i] == " ":
            i += 1
            continue

        mult = 1
        is_multiplier = False
        if s[i].isdigit():
            j = i
            while j < n and s[j].isdigit():
                j += 1
            mult = int(s[i:j])
            i = j
            while i < n and s[i] in " *xX×":
                i += 1
            is_multiplier = True

        matched = False
        for pre, post in BRACKETS:
            if s.startswith(pre, i):
                end_idx = s.find(post, i + len(pre))
                if end_idx == -1:
                    return False
                group = s[i + len(pre):end_idx]
                i = end_idx + len(post)
                matched = True
                break

        if not matched:
            end_idx = s.find(" ", i)
            if end_idx == -1:
                end_idx = n
            group = s[i:end_idx]
            i = end_idx

        if is_multiplier:
            if group not in TALLY_STYLES:
                return False
        else:
            if group in TALLY_STYLES:
                continue
            elif set(group).issubset(ALLOWED_SINGLE) and 1 <= len(group) <= 4:
                continue
            else:
                return False

    return True


def is_tally(to_check: str) -> bool:
    if not isinstance(to_check, str):
        return False
    return validate_tally(to_check)

def type_of(to_check):
    if isinstance(to_check, str):
        if validate_tally(to_check):
            return "tal"
        else:
            return "str"
    elif isinstance(to_check, int):
        return "int"
    elif isinstance(to_check, float):
        return "float"
    elif isinstance(to_check, bool):
        return "bool"
    elif isinstance(to_check, list):
        return "list"
    elif isinstance(to_check, dict):
        return "dict"
    elif isinstance(to_check, set):
        return "set"
    elif isinstance(to_check, tuple):
        return "tuple"
    elif to_check is None:
        return "NoneType"
    elif isinstance(to_check, complex):
        return "complex"
    elif isinstance(to_check, bytes):
        return "bytes"
    elif isinstance(to_check, bytearray):
        return "bytearray"
    elif isinstance(to_check, range):
        return "range"
    elif isinstance(to_check, frozenset):
        return "frozenset"
    elif isinstance(to_check, object):
        return "object"