# -*- coding: utf-8 -*-
"""Fetch live inventory from the project's marketing feed and write status.json.
Marks every 'affordableHousingProgram' (מחיר מטרה) apartment that is no longer
freely available. Keyed by "<building-number>-<apartment-number>" to match the
dashboard cards. Runs locally or in GitHub Actions (stdlib only)."""
import json, urllib.request, datetime, sys

URL = "https://gl-re.co.il/lp/carmei_gat/data.php"
# a status other than these counts as "taken / unavailable" (mirrors the site's own logic)
SOLD = {"sold", "Contract", "Precontract", "negotiation", "notForSale"}

def fetch():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (dira-sync)",
        "Referer": "https://gl-re.co.il/lp/carmei_gat/",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    data = fetch().get("data", [])
    taken, affordable = [], 0
    for x in data:
        if x.get("apartmentCategory") != "affordableHousingProgram":
            continue
        affordable += 1
        bf = x.get("building_floors") or {}
        b = (bf.get("buildings") or {}).get("name")
        if not b:
            continue
        num = b.split("-")[-1]                      # "T1-1" -> "1"
        st = x.get("status")
        tx = x.get("apartments_transactions") or []
        if tx and tx[0].get("status"):
            st = tx[0]["status"]
        if st in SOLD:
            taken.append("%s-%s" % (num, x.get("name")))
    taken = sorted(set(taken))
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # if availability is unchanged, keep the previous timestamp so the file stays
    # byte-identical -> no commit -> no needless Pages rebuild every 10 minutes.
    try:
        with open("status.json", encoding="utf-8") as f:
            old = json.load(f)
        if old.get("taken") == taken and old.get("updated_utc"):
            ts = old["updated_utc"]
    except Exception:
        pass
    out = {
        "updated_utc": ts,
        "affordable_total": affordable,
        "affordable_taken": len(taken),
        "taken": taken,
    }
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")
    print("affordable=%d taken=%d" % (affordable, len(taken)))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:                          # keep last good status.json on failure
        sys.stderr.write("sync failed: %r\n" % e)
        sys.exit(1)
