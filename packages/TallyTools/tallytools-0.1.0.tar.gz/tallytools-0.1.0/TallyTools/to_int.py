__all__ = ["to_int"]

def to_int(tally_str: str) -> int:
    if not isinstance(tally_str, str):
        raise TypeError("Input must be a string")
    s = tally_str.strip().upper()
    if not s:
        return 0

    allowed_chars = set("|/I ()[]{}<>*×-0123456789Xx ")
    if not set(s).issubset(allowed_chars):
        raise ValueError("Tally string contains invalid characters")

    negative = False
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()

    TALLY_STYLES = ["||||/", "|||||", "IIIII"]
    ALLOWED_SINGLE = {"|", "I"}
    BRACKETS = [("(", ")"), ("[", "]"), ("{", "}"), ("<", ">"),
                ("×(", ")"), ("×[", "]"), ("×{", "}"), ("×<", ">"),
                ("*(", ")"), ("*[", "]"), ("*{", "}"), ("*<", ">")]

    i = 0
    total = 0
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
                    raise ValueError(f"Unmatched bracket starting at position {i}")
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
                raise ValueError(f"Invalid multiplier group '{group}' in '{s}' for reduced form")
        else:
            if group not in TALLY_STYLES and (not set(group).issubset(ALLOWED_SINGLE) or len(group) > 4):
                raise ValueError(f"Invalid tally group '{group}' in '{s}'")

        count = 0
        for style in TALLY_STYLES:
            while group.startswith(style):
                count += 5
                group = group[len(style):]
        count += group.count("|") + group.count("I")
        total += count * mult

    return -total if negative else total
