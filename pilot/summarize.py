#!/usr/bin/env python3
"""Summarize a pilot tracker CSV. Prints raw numbers only; with 3 to 5 reps, do not report percentages."""
import csv
import sys
from collections import defaultdict


def summarize(rows):
    reps = defaultdict(lambda: {"before": None, "after": None, "green": set(), "amber": set(), "slips": 0, "notes": []})
    for r in rows:
        d = reps[r["rep"].strip()]
        ev, val = r["event"].strip(), r["value"].strip()
        if ev in ("quiz_before", "quiz_after"):
            score = int(val)
            if not 0 <= score <= 10:
                raise ValueError("quiz score must be 0 to 10: {} {}".format(r["rep"], val))
            d["before" if ev == "quiz_before" else "after"] = score
        elif ev == "green_used":
            d["green"].add(val.lower())
        elif ev == "amber_used":
            d["amber"].add(val.lower())
        elif ev == "slip_caught":
            d["slips"] += 1
        elif ev == "note" and r.get("note", "").strip():
            d["notes"].append(r["note"].strip())
        elif ev not in ("note",):
            raise ValueError("unknown event: " + ev)
    return dict(reps)


def report(reps):
    out = ["Reps in pilot: {}".format(len(reps)), ""]
    pairs = [(d["before"], d["after"]) for d in reps.values() if d["before"] is not None and d["after"] is not None]
    out.append("Quiz score before -> after (each out of 10, different random questions each time):")
    for name in sorted(reps):
        d = reps[name]
        out.append("  {}: {} -> {}".format(name, d["before"] if d["before"] is not None else "n/a", d["after"] if d["after"] is not None else "n/a"))
    if pairs:
        out.append("  Sum of changes across {} reps with both scores: {:+d}".format(len(pairs), sum(a - b for b, a in pairs)))
    allgreen = set().union(*[d["green"] for d in reps.values()]) if reps else set()
    out += ["", "Different green use cases tried (all reps): {}".format(len(allgreen))]
    for name in sorted(reps):
        out.append("  {}: {} green, {} amber".format(name, len(reps[name]["green"]), len(reps[name]["amber"])))
    out += ["", "Near-misses caught: {}".format(sum(d["slips"] for d in reps.values()))]
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: summarize.py tracker.csv")
    with open(sys.argv[1], newline="") as f:
        print(report(summarize(list(csv.DictReader(f)))))
