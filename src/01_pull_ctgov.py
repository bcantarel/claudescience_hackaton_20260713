import json, urllib.request, urllib.parse, time, sys

BASE = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "non-small cell lung cancer",
    "filter.overallStatus": "RECRUITING",
    "pageSize": "1000",
    "countTotal": "true",
}

def fetch(page_token=None):
    p = dict(params)
    if page_token:
        p["pageToken"] = page_token
    url = BASE + "?" + urllib.parse.urlencode(p)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            wait = 2 ** attempt
            print(f"  retry {attempt} after {e} (wait {wait}s)", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit("failed after retries")

all_studies, token, total = [], None, None
while True:
    d = fetch(token)
    if total is None: total = d.get("totalCount")
    all_studies.extend(d.get("studies", []))
    token = d.get("nextPageToken")
    print(f"  fetched {len(all_studies)}/{total}", file=sys.stderr)
    if not token: break

json.dump(all_studies, open("data/nsclc_recruiting.json", "w"))
print(f"Saved {len(all_studies)} studies. Expected total: {total}")
