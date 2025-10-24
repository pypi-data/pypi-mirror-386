# TallyTools

A simple and powerful Python library for converting, validating, and performing arithmetic with tally marks.

TallyTools provides a comprehensive toolkit for handling tally mark notation in your Python projects. Whether you need to convert a number into a tally string, parse a complex tally expression back into an integer, or perform mathematical operations, this library has you covered.

It's designed to be flexible and intuitive, understanding various tally styles (like `||||/` or `|||||`), shorthand multipliers (like `3 * (||||/)`), and even negative numbers right out of the box.

# Key Features

**Integer to Tally**: Convert any integer into a customizable tally mark string.

**Tally to Integer**: Parse complex tally strings back into integers, automatically handling different styles, spacing, and multipliers.

**Tally Arithmetic**: Perform math directly! Add, subtract, multiply, and compare tally marks using the powerful TallyMark class.

**Validation**: Quickly check if a string is a valid tally mark representation.

**Inspection**: Analyze tally strings to count groups, find the largest group, and more.

# Installation

Install TallyTools directly from PyPI:

```bash
pip install TallyTools
```



# Quick Start: Basic Conversions

TallyTools is easy to use for simple conversions. The two main functions you'll need are `to_tally` and `to_int`.

### 1. From a Number to Tally Marks

Use the `to_tally()` function to convert any integer into a tally string.

```py
from TallyTools import to_tally

# Convert the number 17 into tally marks
tally_string = to_tally(17)

print(f"The number 17 is: {tally_string}")

# --- Output ---
# The number 17 is: ||||/ ||||/ ||||/ ||
```


### 2. From Tally Marks to a Number

Use the `to_int()` function to convert a tally string back into an integer. It's smart and can handle many different formats.

```py
from TallyTools import to_int

# It understands standard groups
val_1 = to_int("||||/ |||")
print(f"'||||/ |||' is the number {val_1}")

# It's not fussy about style or spacing
val_2 = to_int("||||| IIIII  ||")
print(f"'||||| IIIII  ||' is the number {val_2}")

# It even understands shorthand multipliers and brackets!
val_3 = to_int("3 * (||||/) ||")
print(f"'3 * (||||/) ||' is the number {val_3}")

# --- Output ---
# '||||/ |||' is the number 8
# '||||| IIIII  ||' is the number 12
# '3 * (||||/) ||' is the number 17
```


# Advanced Usage: The TallyMark Class

For more power, TallyTools provides a TallyMark class. Think of it as a special object that holds both the string version and the integer version of a tally.

The best part? You can do math with them directly.

```py
from TallyTools import TallyMark

# Create TallyMark objects from integers, strings, or lists
a = TallyMark(12)
b = TallyMark("||||/ ||")  # This is 7

print(f"Object 'a' is: {a} (Value: {a.value})")
print(f"Object 'b' is: {b} (Value: {b.value})")
print("-" * 20)

# --- Perform Arithmetic ---
addition = a + b
print(f"{a} + {b}  =  {addition}")

subtraction = a - b
print(f"{a} - {b}  =  {subtraction}")

multiplication = b * 3
print(f"({b}) * 3  =  {multiplication}")

# --- Perform Comparisons ---
print("-" * 20)
print(f"Is {a} > {b}?  ->  {a > b}")
print(f"Is {a} == {b}? ->  {a == b}")

# You can always get the integer or string back
print(f"Final value as integer: {addition.value}")
print(f"Final value as string:  {addition.raw}")
```


Output:
```
Object 'a' is: ||||/ ||||/ || (Value: 12)
Object 'b' is: ||||/ || (Value: 7)
--------------------
||||/ ||||/ || + ||||/ ||  =  ||||/ ||||/ ||||/ ||||
||||/ ||||/ || - ||||/ ||  =  ||||/
(||||/ ||) * 3  =  ||||/ ||||/ ||||/ ||||/ |
--------------------
Is ||||/ ||||/ || > ||||/ ||?  ->  True
Is ||||/ ||||/ || == ||||/ ||? ->  False
Final value as integer: 19
Final value as string:  ||||/ ||||/ ||||/ ||||
```


# API Documentation

Here is a brief overview of the main functions and classes available.

### Core Functions

- `to_tally(n: int, expand=True, tally_style="fslash", ...)`

    - Converts an integer `n` to a tally string.

    - `expand=False`: Uses multiplier notation (e.g., `3(||||/)`).

    - `tally_style`: Changes the group of five. Can be `"fslash" (||||/)`, `"pipe" (|||||)`, or `"roman" (IIIII)`.

- `to_int(tally_str: str) -> int`

    - Converts any valid tally string into an integer. Handles multipliers, negatives, and different tally styles.

# The `TallyMark` Class

- `TallyMark(value)`

    - The constructor can accept an `int`, a `str`, or a `list` of tally strings.

- **Operators**: Supports all standard arithmetic and comparison operators:

`+`, `-`, `*`, `/` (division performs floor division)

`==`, `!=`, `>`, `<`, `>=`, `<=`

- **Properties**:

    - `.value`: Get the integer value (e.g., `12`).

    - `.raw`: Get the raw string representation (e.g., `||||/ ||||/ ||`).

### Utility Functions

- `is_tally(to_check: str) -> bool`

    - Returns `True` if the string is a valid tally, `False` otherwise.

- `type_of(to_check)`

    - Returns the type of the input as a string. Identifies valid tally strings as `"tal"`.

- `count_groups(tally_str: str) -> int`

    - Counts the number of tally groups (e.g., `||||/ ||` has 2 groups).

- `list_groups(tally_str: str) -> list`

    - Returns a list of all groups (e.g., `['||||/', '||']`).

- `min_group(tally_str: str) -> int`

    - Finds the value of the smallest group in the string.

- `max_group(tally_str: str) -> int`

    - Finds the value of the largest group in the string.

# License

This project is licensed under the MIT License. See the `LICENSE` file for more details.