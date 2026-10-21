import os, re, subprocess, sys

TOKEN = os.environ["METRICS_TOKEN"]
OWNER, REPO = "lianbeast", "lianbeast"
BRANCH = "main"
CACHE = ".cache"
STAGING = "README.md.tmp"

if not os.path.exists(STAGING):
    print("no staging file; nothing to cache")
    sys.exit(0)

os.makedirs(CACHE, exist_ok=True)
text = open(STAGING, encoding="utf-8").read()

# With output_action: "none" the metrics action rewrites every cacheable <img>
# to a github.com blob URL (github.com/.../blob/main/.cache/<name>.<ext>) but
# never writes the file itself — it only saves the rendered markdown to the
# runner mount. Fetch each blob through the API, materialise it in .cache/,
# and point the <img> at the raw URL GitHub renders inline.
#
# Two source forms are handled: the base64 data URI the template produces
# (class="metrics-cacheable"), and the blob URL the action rewrites it to.
b64_re = re.compile(
    r'<img class="metrics-cacheable" data-name="(?P<name>[^"]+)" '
    r'src="data:image/(?P<fmt>svg\+xml|jpeg|png);base64,(?P<content>[^"]+)"'
)
blob_re = re.compile(
    r'<img src="https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/'
    r'(?P<branch>[^/]+)/(?P<path>[^"]+)"'
)

def fetch_blob(path):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    out = subprocess.run(
        ["curl", "-sS", "-H", f"Authorization: token {TOKEN}", "-H",
         "Accept: application/vnd.github.v3.raw", url],
        capture_output=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"curl failed for {path}: {out.stderr.decode()}")
    return out.stdout

count = 0

def repl_b64(m):
    global count
    name = m.group("name")
    fmt = m.group("fmt").replace("+", "")
    content = m.group("content")
    local = os.path.join(CACHE, f"{name}.{fmt}")
    with open(local, "wb") as f:
        f.write(base64.b64decode(content))
    count += 1
    return f'<img src="https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{CACHE}/{name}.{fmt}">'

def repl_blob(m):
    global count
    path = m.group("path")
    local = os.path.join(CACHE, os.path.basename(path))
    data = fetch_blob(path)
    with open(local, "wb") as f:
        f.write(data)
    count += 1
    return f'<img src="https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{CACHE}/{os.path.basename(path)}">'

text = b64_re.sub(repl_b64, text)
text = blob_re.sub(repl_blob, text)

# Fallbacks for any leftover blob URLs and the broken avatar URL.
text = re.sub(
    r'https://github\.com/lianbeast/lianbeast/blob/main/\.cache/',
    'https://raw.githubusercontent.com/lianbeast/lianbeast/main/.cache/',
    text,
)
text = text.replace(
    "https://github.com/lianbeast?avatar=1",
    "https://avatars.githubusercontent.com/lianbeast?s=240&v=4",
)

open(STAGING, "w", encoding="utf-8").write(text)
print(f"cached {count} metrics images into {CACHE}/")
