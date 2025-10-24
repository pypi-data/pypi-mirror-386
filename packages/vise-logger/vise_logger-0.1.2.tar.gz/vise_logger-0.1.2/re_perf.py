import re, time, random, string
pat = re.compile(r'(?<!\w)@(?P<body>[A-Za-z0-9._-]{2,64})(?!\w)', re.ASCII)

N = 1_000_000
text = "@alice " + "".join(random.choices(string.ascii_letters + string.digits + " ._-@", k=N-7))

t0 = time.perf_counter()
cnt = sum(1 for _ in pat.finditer(text))
t1 = time.perf_counter()
print("matches:", cnt, "seconds:", t1 - t0, "MB/s:", len(text)/(t1-t0)/1e6)