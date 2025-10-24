
from .checkers import validate_tally, is_tally, type_of
from .to_int import to_int
from .to_tally import to_tally

__all__ = ["min_group", "max_group", "count_groups", "list_groups", "TallyMark"]

def min_group(tally_str: str) -> int:
    tally_str_list = tally_str.split()
    int_list = []

    for grp in tally_str_list:
        mult = 1
        i = 0

        while i < len(grp) and grp[i].isdigit():
            i += 1

        if i > 0:
            mult = int(grp[:i])
            while i < len(grp) and grp[i] in " *xX×":
                i += 1
            grp = grp[i:]
        if grp.startswith(("(", "[", "{", "<", "×(", "×[", "×{", "×<", "*(", "*[", "*{", "*<")):
            grp = grp[grp.find("(")+1 if "(" in grp else 0 : -1]
        int_list.append(to_int(grp) * mult)

    return min(int_list) if int_list else 0

def max_group(tally_str: str) -> int:
    tally_str_list = tally_str.split()
    int_list = []

    for grp in tally_str_list:
        mult = 1
        i = 0

        while i < len(grp) and grp[i].isdigit():
            i += 1

        if i > 0:
            mult = int(grp[:i])
            while i < len(grp) and grp[i] in " *xX×":
                i += 1
            grp = grp[i:]
        if grp.startswith(("(", "[", "{", "<", "×(", "×[", "×{", "×<", "*(", "*[", "*{", "*<")):
            grp = grp[grp.find("(")+1 if "(" in grp else 0 : -1]
        int_list.append(to_int(grp))

    return max(int_list) if int_list else 0

def list_groups(tally_str: str, tally_style="fslash"):
    if not isinstance(tally_str, str):
        raise TypeError("Input must be a string")
    s = tally_str.strip().upper()
    if not s:
        return []
    if not validate_tally(s):
        raise ValueError("Invalid tally string")
    n = to_int(s)
    negative = n < 0
    n = abs(n)
    fives, rem = divmod(n, 5)
    style = ""
    if tally_style == "fslash":
        five = "||||/"
        style = "|"
    elif tally_style == "pipe":
        five = "|||||"
        style = "|"
    elif tally_style == "roman":
        five = "IIIII"
        style = "I"
    else:
        raise ValueError("Invalid tally style")
    groups = [five] * fives
    if rem:
        groups.append(style * rem)
    if negative:
        if groups:
            groups[0] = "-" + groups[0]
        else:
            groups = ["-"]
    return groups


def count_groups(tally_str: str) -> int:
    tally_str_list = tally_str.split()
    count = 0

    for grp in tally_str_list:
        mult = 1
        i = 0

        while i < len(grp) and grp[i].isdigit():
            i += 1

        if i > 0:
            mult = int(grp[:i])
        count += mult

    return count

class TallyMark:
    def __init__(self, tally_str):
        if isinstance(tally_str, int):
            self.value = tally_str
            self.raw = to_tally(tally_str)
        elif isinstance(tally_str, (list, tuple)):
            self.raw = " ".join(str(x) for x in tally_str)
            self.value = sum(to_int(x) for x in tally_str)
        else:
            if not isinstance(tally_str, str):
                tally_str = str(tally_str)
            if not validate_tally(tally_str):
                raise ValueError(f"Invalid tally mark input: {tally_str}")
            self.raw = tally_str.strip().upper()
            self.value = to_int(tally_str)

    def __repr__(self):
        return f"TallyMark('{self.raw}')"

    def __str__(self):
        return self.raw

    def __int__(self):
        return self.value

    def __add__(self, other):
        return TallyMark(self.value + TallyMark(other).value)

    def __sub__(self, other):
        return TallyMark(self.value - TallyMark(other).value)

    def __mul__(self, other):
        return TallyMark(self.value * TallyMark(other).value)

    def __truediv__(self, other):
        return TallyMark(self.value // TallyMark(other).value)

    def __eq__(self, other):
        return self.value == TallyMark(other).value

    def __lt__(self, other):
        return self.value < TallyMark(other).value

    def __le__(self, other):
        return self.value <= TallyMark(other).value

    def __gt__(self, other):
        return self.value > TallyMark(other).value

    def __ge__(self, other):
        return self.value >= TallyMark(other).value

    def min_group(self):
        return min_group(self.raw)

    def max_group(self):
        return max_group(self.raw)

    def count_groups(self):
        return count_groups(self.raw)

    def list_groups(self):
        return list_groups(self.raw)
    
