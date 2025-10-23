import re

RES_FROM_URL = re.compile(r'-(\d{3,4})\.mp4\b')
# grab the whole JS object literal for `flashvars = { ... }`
FLASHVARS_BLOCK = re.compile(r"var\s+flashvars\s*=\s*\{(?P<body>.*?)\}\s*;", re.DOTALL)
# simple 'key': 'value' pairs (single or double quotes), integers/floats allowed
KV_PAIR = re.compile(
    r"""(?P<key>['"][^'"]+['"])\s*:\s*(?P<val>(?:['"][^'"]*['"])|(?:-?\d+(?:\.\d+)?))\s*,?""",
    re.DOTALL)
