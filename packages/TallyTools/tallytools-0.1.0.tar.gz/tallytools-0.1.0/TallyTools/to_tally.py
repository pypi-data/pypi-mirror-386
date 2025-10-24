__all__ = ["to_tally"]

def to_tally(n, expand=True, tally_style="fslash", group_format="rbrackets", group_individual=False) -> str:
    if not n:
        raise ValueError("Input integer cannot be empty")
    if n == 0:
        return ""

    fives, extra = divmod(abs(n), 5)

    TALLY_STYLES = {
        "fslash": "||||/",
        "pipe": "|||||",
        "roman": "IIIII",
    }

    GROUP_FORMATS = {
        None: ("", ""),
        "none": ("", ""),
        "rbrackets": ("(", ")"),
        "sbrackets": ("[", "]"),
        "cbrackets": ("{", "}"),
        "abrackets": ("<", ">"),
        "xrbrackets": (" × (", ")"),
        "xsbrackets": (" × [", "]"),
        "xcbrackets": (" × {", "}"),
        "xabrackets": (" × <", ">"),
        "*rbrackets": (" * (", ")"),
        "*sbrackets": (" * [", "]"),
        "*cbrackets": (" * {", "}"),
        "*abrackets": (" * <", ">"),
    }

    if tally_style not in TALLY_STYLES:
        raise ValueError(f"Unknown tally_style: {tally_style}")
    if group_format not in GROUP_FORMATS and not (isinstance(group_format, tuple) and len(group_format) == 2):
        raise ValueError(f"Unknown group_format: {group_format}")

    std5 = f"{TALLY_STYLES[tally_style]} "
    pipe = "|"
    pre_grouper, post_grouper = GROUP_FORMATS.get(group_format, group_format if isinstance(group_format, tuple) else ("(", ")"))

    extra_pipes = pipe * extra

    if group_individual and expand:
        std5 = f"{pre_grouper}{TALLY_STYLES[tally_style]}{post_grouper} "
        extra_pipes = f"{pre_grouper}{pipe * extra}{post_grouper}"
    elif group_individual and not expand:
        std5 = f"{pre_grouper}{TALLY_STYLES[tally_style]}{post_grouper}"
        extra_pipes = f"{pre_grouper}{pipe * extra}{post_grouper}"
    elif not group_individual and expand:
        std5 = f"{TALLY_STYLES[tally_style]} "
    elif not group_individual and not expand:
        std5 = f"{TALLY_STYLES[tally_style]}"

    if n < 0:
        if expand:
            return f"-{std5 * fives}{extra_pipes}"
        else:
            return f"-{fives}{pre_grouper}{std5}{post_grouper} {extra_pipes}"
    if n > 0:
        if expand:
            return f"{std5 * fives}{extra_pipes}"
        else:
            return f"{fives}{pre_grouper}{std5}{post_grouper} {extra_pipes}"