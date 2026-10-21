import re, base64, os, sys

fname = "README.md.tmp"
if not os.path.exists(fname):
    print("no staging file; nothing to cache")
    sys.exit(0)

text = open(fname, encoding="utf-8").read()
os.makedirs(".cache", exist_ok=True)

# Metrics marks embed images as cacheable with a base64 data URI when it does
# not commit them itself (output_action: "none"). Decode them back to files
# and point the <img> at the raw URL GitHub will render inline.
pattern = re.compile(
    r'<img class="metrics-cacheable" data-name="(?P<name>[^"]+)" '
    r'src="data:image/(?P<fmt>svg\+xml|jpeg|png);base64,(?P<content>[^"]+)"'
)

def repl(m):
    name = m.group("name")
    fmt = m.group("fmt").replace("+", "")
    content = m.group("content")
    path = f".cache/{name}.{fmt}"
    with open(path, "wb") as f:
        f.write(base64.b64decode(content))
    return f'<img src="https://raw.githubusercontent.com/lianbeast/lianbeast/main/.cache/{name}.{fmt}">'

count = len(pattern.findall(text))
text = pattern.sub(repl, text)

# Leftover blob URLs and the broken avatar URL, if any.
text = re.sub(
    r'https://github.com/lianbeast/lianbeast/blob/main/\.cache/',
    'https://raw.githubusercontent.com/lianbeast/lianbeast/main/.cache/',
    text,
)
text = text.replace(
    "https://github.com/lianbeast?avatar=1",
    "https://avatars.githubusercontent.com/lianbeast?s=240&v=4",
)

open(fname, "w", encoding="utf-8").write(text)
print(f"cached {count} metrics images into .cache/")
