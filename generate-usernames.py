from os.path import exists
import csv
import re
import sys


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


def convert_to_usernames(names, fstring):
    """
    Convert cleaned names to usernames using the provided f-string template.

    Rules:
    - For names with 3+ parts: first = parts[0], middle = parts[1], last = parts[-1]
    - Names with fewer than 3 parts are skipped.
    - Supports {first}, {f}, {middle}, {m}, {last}, {l}
    """
    usernames = []
    skipped = 0

    for name in names:
        parts = name.split(' ')
        if len(parts) < 3:
            skipped += 1
            continue

        first = parts[0]
        middle = parts[1]
        last = parts[-1]

        # Build initials
        f = first[0] if first else ''
        m = middle[0] if middle else ''
        l = last[0] if last else ''

        # Prepare template values (all lower-cased already)
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
        except KeyError as e:
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
    - If a name has 3+ parts:
        * First  = part 1
        * Middle = part 2
        * Last   = last part (the final token)
      (Any parts between part 2 and the last part are ignored.)
    - If a name has fewer than 3 parts (no middle name), it is skipped.

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

    python3 generate-usernames.py "{f}{m}{last}@acme.com" employees.csv > output.txt
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
print(f"\n[warning] Skipped {skipped_count} name(s) without a detectable middle name.", file=sys.stderr)
