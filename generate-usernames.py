from os.path import exists
import csv
import re
import sys


def extract_names(filename):
    """
    Returns the list of names found in the first column of a given CSV or text file.
    """
    names = []

    if exists(filename):
        with open(filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in csvreader:
                if row:
                    names.append(row[0])

    names = [name.strip() for name in names]
    return names


def clean_and_sort_names(names):
    """Remove strings such as titles that are not part of the name."""
    # Remove parenthetical notes, trailing credentials, and leading titles
    titles_suffixes = r'\([^)]+\)?|, ?[a-z]?[A-Z.]+|^(Dr|Mrs?|Ms)\.? ?'
    names = [re.sub(titles_suffixes, '', name) for name in names]

    # Keep only letters and spaces; drop "LinkedIn Member" rows
    non_names = r'[^A-Za-z ]|LinkedIn Member'
    names = [re.sub(non_names, '', name) for name in names]

    # Normalize whitespace and lowercase
    multiple_spaces = r' +'
    names = [re.sub(multiple_spaces, ' ', name).strip() for name in names]
    names = [name.lower() for name in names]

    # Drop empties and dedupe/sort
    names = [n for n in names if n]
    names = sorted(set(names))

    return names


def convert_to_usernames(names, fstring):
    """
    Convert cleaned names to usernames based on a format string.

    Requires a middle name: only names with 3+ parts are used.
    When 3+ parts are present:
        first  = first token
        middle = second token
        last   = last token (explicitly the final token)
    Any tokens between the middle and last are ignored by design.

    Returns (usernames_list, skipped_count).
    """
    usernames = []
    skipped = 0

    for name in names:
        parts = name.split()
        if len(parts) < 3:
            skipped += 1
            continue

        first = parts[0]
        middle = parts[1]
        last = parts[-1]

        f = first[0] if first else ''
        m = middle[0] if middle else ''
        l = last[0] if last else ''

        template_values = {
            'first': first,
            'middle': middle,
            'last': last,
            'f': f,
            'm': m,
            'l': l,
        }

        try:
            usernames.append(fstring.format(**template_values))
        except KeyError as e:
            # If the template references unknown keys, surface a clear error and exit.
            print(f"Error: template references unknown field {e}. "
                  f"Allowed fields are {{first}}, {{middle}}, {{last}}, {{f}}, {{m}}, {{l}}.",
                  file=sys.stderr)
            sys.exit(1)

    return usernames, skipped


usage = """
generate-usernames.py
=====================

Generates a list of usernames or email addresses from a list of names.

The input file may be either a text file with one name on each line or a CSV
file that contains the names in the first column.

Parsing rules:
  - A name must contain a middle part to be used (i.e., at least 3 tokens).
  - For names with 3+ tokens: first = first token, middle = second token,
    last = *last* token. Tokens in between are ignored.

The following fields may be used in the username template:
    - {first}   : First name
    - {middle}  : Middle name
    - {last}    : Last name
    - {f}       : First initial
    - {m}       : Middle initial
    - {l}       : Last initial

Output is printed to stdout, so just redirect to a file to save the output.
A warning with the number of skipped names (no detected middle) is printed to stderr.

Usage: python3 generate-usernames
