"""Tech occupations in the National Occupational Classification (NOC 2021).

The list is explicit on purpose: filtering by a code prefix such as ``212``
would also pull in architects (21200) and urban planners (21202).
"""

from __future__ import annotations

#: NOC 2021 code -> (official occupation name, family used in the analysis)
TECH_OCCUPATIONS: dict[str, tuple[str, str]] = {
    "21210": ("Mathematicians, statisticians and actuaries", "Data"),
    "21211": ("Data scientists", "Data"),
    "21223": ("Database analysts and data administrators", "Data"),
    "21230": ("Computer systems developers and programmers", "Software"),
    "21231": ("Software engineers and designers", "Software"),
    "21232": ("Software developers and programmers", "Software"),
    "22222": ("Information systems testing technicians", "Software"),
    "21233": ("Web designers", "Web"),
    "21234": ("Web developers and programmers", "Web"),
    "21220": ("Cybersecurity specialists", "Security"),
    "21221": ("Business systems specialists", "IT & systems"),
    "21222": ("Information systems specialists", "IT & systems"),
    "21311": ("Computer engineers (except software engineers and designers)", "Networks & support"),
    "22220": ("Computer network and web technicians", "Networks & support"),
    "22221": ("User support technicians", "Networks & support"),
}
