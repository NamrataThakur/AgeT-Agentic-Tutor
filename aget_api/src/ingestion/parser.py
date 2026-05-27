#This file handles the parsing of the extracted wikipedia content to properly preserve the LaTeX math part:

import re

def normalize_whitespace(text: str) -> str:

    # collapse excessive newlines
    text = re.sub(r"\n+", "\n", text)

    # collapse spaces
    text = re.sub(r"\s+", " ", text)

    #To Consider text only after this marker. This makes sure we are not embedding the inital non-important contents:
    marker = "From Wikipedia, the free encyclopedia"

    if marker in text:
        text = text.split(marker, 1)[1]

    #To make sure we dont include the content after these markers as they are not important also:
    end_markers = [
                    "References",
                    "External links",
                    "Sources",
                    "See also",
                ]

    for marker in end_markers:

        if marker in text:
            text = text.split(marker, 1)[0]

    return text.strip()



def replace_displaystyle(text: str) -> str:
    """
    Convert:
        {\displaystyle ...}
    into:
        $$ ... $$

    Handles nested braces correctly.
    """

    result = []

    i = 0

    while i < len(text):

        start = text.find(r"{\displaystyle", i)

        # no more latex
        if start == -1:
            result.append(text[i:])
            break

        # ---------- TEXT BEFORE EQUATION ----------

        before = text[i:start]

        # remove trailing fragmented math/noise
        before = re.sub(
            r"""
            (
                [A-Za-z0-9
                βμσΦπθλωαδγΩ
                εητκ
                \[\]\(\)=+\-/*^,.;:{}_\\\s
                ]{5,}
            )$
            """,
            "",
            before,
            flags=re.VERBOSE,
        )

        result.append(before)

        # ---------- FIND MATCHING BRACE ----------

        brace_count = 0
        j = start

        while j < len(text):

            if text[j] == "{":
                brace_count += 1

            elif text[j] == "}":
                brace_count -= 1

                if brace_count == 0:
                    break

            j += 1

        latex = text[start + len(r"{\displaystyle"):j].strip()

        latex = re.sub(r"\s+", " ", latex)

        result.append(f" $$ {latex} $$ ")

        i = j + 1

    text = "".join(result)

    # cleanup whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()