"""Ordered education and experience levels used in Job Bank postings.

Job Bank labels are long and sort alphabetically in an unhelpful order. Each
label maps to a short name and a rank so tables and charts read from the
lowest to the highest requirement. "College/CEGEP" is kept apart from the two
labels with an explicit program length because the source does not say how
they differ.
"""

from __future__ import annotations

#: Job Bank label -> (short label, rank)
EDUCATION_LEVELS: dict[str, tuple[str, int]] = {
    "No degree, certificate or diploma": ("No formal education", 0),
    "Secondary (high) school graduation certificate": ("High school", 1),
    "Other trades certificate or diploma": ("Trades certificate", 2),
    "Registered Apprenticeship certificate": ("Apprenticeship", 3),
    "College, CEGEP or other non-university certificate or diploma from a program "
    "of 3 months to less than 1 year": ("College, under 1 year", 4),
    "College, CEGEP or other non-university certificate or diploma from a program "
    "of 1 year to 2 years": ("College, 1 to 2 years", 5),
    "College/CEGEP": ("College/CEGEP, length not stated", 6),
    "Bachelor's degree": ("Bachelor's degree", 7),
    "Master's degree": ("Master's degree", 8),
    "Degree in medicine, dentistry, veterinary medicine or optometry": (
        "Medicine or related degree",
        9,
    ),
    "Earned doctorate degree": ("Doctorate", 10),
}

#: Job Bank label -> (short label, rank)
EXPERIENCE_LEVELS: dict[str, tuple[str, int]] = {
    "No experience": ("None", 0),
    "1 to less than 7 months": ("Under 7 months", 1),
    "7 months to less than 1 year": ("7 to 12 months", 2),
    "1 year to less than 2 years": ("1 to 2 years", 3),
    "2 years to less than 3 years": ("2 to 3 years", 4),
    "3 years to less than 5 years": ("3 to 5 years", 5),
    "5 years or more": ("5 years or more", 6),
}

#: Rank given to labels missing from the tables above, so they sort last.
UNKNOWN_RANK = 99
