"""Define the syntax of an exact npm semantic version."""

import re

NUMBER = r"(?:0|[1-9][0-9]*)"
IDENT = r"[0-9A-Za-z-]+"
PRE = rf"(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
    rf"(?:-{PRE}(?:\.{PRE})*)?(?:\+{IDENT}(?:\.{IDENT})*)?"
)
