from os.path import exists
import csv
import re
import sys
from string import Formatter


def extract_names(filename):
    """
    Returns the list of names found in the first column of a given CSV file.
    """

    names = []

    if exists(filename):
        with open(filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in csvreader:
                # Handle empty lines gracefully
                if not row:
                    continue
                names.append(row[0])

    names = [name.strip() for name in names]

    return names


def clean_and_sort_names(names):
    """Remove strings such as titles that are not part of the name."""

    titles_suffixes = r'\([^)]+\)?|, ?[a-z]?[A-Z.]+|^(Dr|Mrs?|Ms)\.? ?'
    names = [re.sub(titles_suffixes, '', name) for name in names]

    non_names = r'[^A-Za-z ]|LinkedIn Member'
    names = [re.sub(non_names, '', name) for name in names]

    multiple_spaces = r' +'
    names = [re.sub(multiple_spaces, ' ', name).strip() for name in names]

    names = [name.lower() for name in names]

    while '' in names:
        names.remove('')

    names = list(set(names))
    names.sort()

    return names


def _fields_in_template(fstring):
    """Return a set of field names referenced in the f-string template."""
    fields = set()
    for literal_text, field_name, format_spec, conversion in Formatter().parse(fstring):
        if field_name:  # may be None for literal-only segments
            fields.add(field_name)
    return fields


def convert_to_usernames(names, fstring):
    """
    Convert cleaned names to usernames using the provided f-string template.

    Rules:
    - Skip a name only if the template requires a component that's missing:
        * If {middle} or {m} is in the template, the name must have 3+ parts.
        * If {last} or {l}  is in the template, the name must have 2+ parts.
        * If {first} or {f} is in the template, the name must have 1+ parts.
      Otherwise, use whatever parts exist (unset parts become empty strings).
    - For names with 3+ parts: first = parts[0], middle = parts[1], last = parts[-1]
      (Any parts between part 2 and the last part are ignored.)
    - Supports {first}, {f}, {middle}, {m}, {last}, {l}
    """
    usernames = []
    skipped = 0

    fields = _fields_in_template(fstring)
    requires_first = ('first' in fields) or ('f' in fields)
    requires_middle = ('middle' in fields) or ('m' in fields)
    requires_last = ('last' in fields) or ('l' in fields)

    for name in names:
        parts = name.split(' ')
        n = len(parts)

        # Check required parts against available tokens
        if requires_first and n < 1:
            skipped += 1
            continue
        if requires_last and n < 2:
            skipped += 1
            continue
        if requires_middle and n < 3:
            skipped += 1
            continue

        # Map parts (use empty strings for non-required/missing components)
        first = parts[0] if n >= 1 else ''
        last = parts[-1] if n >= 2 else ''
        middle = parts[1] if n >= 3 else ''

        # Build initials
        f = first[0] if first else ''
        m = middle[0] if middle else ''
        l = last[0] if last else ''

        template_values = {
            'first': first,
            'f': f,
            'middle': middle,
            'm': m,
            'last': last,
            'l': l
        }

        try:
            usernames.append(fstring.format(**template_values))
        except KeyError:
            # If the template contains unexpected fields, treat as skip
            skipped += 1
            continue

    return usernames, skipped


usage = """
generate-usernames.py
=====================

Generates a list of usernames or email addresses from a list of first, middle, and last
names.

The input file may be either a text file with one name on each line or a CSV
file that contains the names in the first column.

Name parsing:
    - For 3+ part names:
        * First  = part 1
        * Middle = part 2
        * Last   = last part (the final token)
      (Any parts between part 2 and the last part are ignored.)

Skipping behavior (updated):
    - A name is skipped ONLY if the template requires a component that is missing:
        * Requires {middle}/{m}  -> input must have 3+ parts
        * Requires {last}/{l}    -> input must have 2+ parts
        * Requires {first}/{f}   -> input must have 1+ parts
      If the template does NOT reference a component, that component is not required.

The following fields may be used in the username template:
    - {first}   : First name
    - {middle}  : Middle name
    - {last}    : Last name
    - {f}       : First initial
    - {m}       : Middle initial
    - {l}       : Last initial

Output is printed to stdout, so just redirect to a file to save the output.
At the end, a warning is printed to stderr with the number of skipped names.

Usage: python3 generate-usernames.py <Template> <First Middle Last Name File(s)>

Example:

    # Middle required (names with no middle will be skipped)
    python3 generate-usernames.py "{f}{m}{last}@acme.com" employees.csv > output.txt

    # Middle not required (two-part names are accepted)
    python3 generate-usernames.py "{f}{last}@acme.com" employees.csv > output.txt
"""

if len(sys.argv) < 3 or '-h' in sys.argv or '--help' in sys.argv:
    print(usage)
    exit()

name_files = sys.argv[2:]
fstring = sys.argv[1]

names = []

for filename in name_files:
    names += extract_names(filename)

names = clean_and_sort_names(names)

usernames, skipped_count = convert_to_usernames(names, fstring)
usernames = list(set(usernames))
usernames.sort()

print("\n".join(usernames))

# Print warning about skipped names to stderr
print(f"\n[warning] Skipped {skipped_count} name(s) due to missing required parts for the chosen template.", file=sys.stderr)
