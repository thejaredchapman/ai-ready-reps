#!/usr/bin/env python3
"""Account Brief: a reference implementation of the AI Ready Reps amber guardrails.

It builds a short research brief about a company from its PUBLIC web pages.
The four guardrails are enforced in code, not in a policy document:

  1. Public data only   - https only, no logins, no private or internal hosts,
                          emails and phone numbers are stripped, robots.txt is obeyed.
  2. Read-only research - the only network call is an HTTP GET. There is no code path
                          that writes to a CRM, a mailbox, or any other system.
  3. Every source cited - each claim is a verbatim sentence plus its URL. A checker
                          re-reads the page text and drops any claim it cannot find.
  4. A person approves  - the brief is a DRAFT until a human types APPROVE at a terminal.
                          Export refuses unapproved or edited briefs. Nothing is ever sent.

Standard library only. No AI model is called. A model could be added to the
drafting step; the verify_claims() check would apply to its output unchanged.
"""
import argparse
import datetime
import hashlib
import html.parser
import ipaddress
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

USER_AGENT = "AccountBriefReference/1.0 (read-only research; contact: see repository README)"
MAX_PAGES = 5
MAX_BYTES = 1_000_000
TIMEOUT = 10
MAX_CLAIMS = 12

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
# Topics a rep asks about first. Order is the order shown in the brief.
TOPICS = [
    ("What they do", re.compile(r"\b(we (?:provide|build|help|offer|make|are)|is a (?:leading )?\w+ (?:company|platform|provider)|our (?:mission|platform|products?|solutions?))\b", re.I)),
    ("Size and growth", re.compile(r"\b(\d[\d,.]*\s?(?:\+|million|billion|employees|customers|countries|offices|locations)|founded in \d{4}|headquartered|since \d{4})", re.I)),
    ("Recent news", re.compile(r"\b(announce[sd]?|launch(?:ed|es)?|acquir(?:ed|es)|partnership|raised|opens?|appoint(?:ed|s)|released?)\b", re.I)),
]


class RefusedError(Exception):
    """Raised when a guardrail blocks an action. The message says which one and why."""


# ---------- guardrail 1: public data only ----------

def check_public_url(url, resolver=socket.getaddrinfo):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https":
        raise RefusedError("public-data: only https URLs are allowed: " + url)
    if p.username or p.password:
        raise RefusedError("public-data: URLs with credentials are not allowed")
    if p.port not in (None, 443):
        raise RefusedError("public-data: non-standard ports are not allowed")
    host = p.hostname or ""
    if not host or "." not in host or host.endswith((".local", ".internal", ".lan", ".corp")):
        raise RefusedError("public-data: not a public hostname: " + host)
    try:
        infos = resolver(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise RefusedError("public-data: host does not resolve: " + host)
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise RefusedError("public-data: host resolves to a non-public address: " + host)
    return url


def strip_personal(text):
    """Remove emails and phone numbers. A company page is public; a person's contact details are not ours to collect."""
    return PHONE_RE.sub("[removed]", EMAIL_RE.sub("[removed]", text))


class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "form", "head"}

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth and data.strip():
            self.parts.append(data.strip())


def page_text(raw_html):
    t = _Text()
    t.feed(raw_html)
    return strip_personal(re.sub(r"\s+", " ", " ".join(t.parts)))


# ---------- guardrail 2: read-only research ----------

def http_get(url):
    """The ONLY network function in this program. GET, no cookies, no auth, size-capped."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        ctype = r.headers.get("Content-Type", "")
        if "html" not in ctype:
            raise RefusedError("read-only: not an HTML page: " + url)
        return r.read(MAX_BYTES).decode("utf-8", "replace")


def allowed_by_robots(url, fetch=http_get):
    p = urllib.parse.urlsplit(url)
    robots = "{}://{}/robots.txt".format(p.scheme, p.netloc)
    rp = urllib.robotparser.RobotFileParser()
    try:
        req = urllib.request.Request(robots, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            rp.parse(r.read(MAX_BYTES).decode("utf-8", "replace").splitlines())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False
        return True  # no robots.txt means no restrictions
    except Exception:
        return False  # cannot tell, so do not fetch
    return rp.can_fetch(USER_AGENT, url)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def collect(urls, fetch=http_get, robots=allowed_by_robots, resolver=socket.getaddrinfo, log=None):
    if len(urls) > MAX_PAGES:
        raise RefusedError("read-only: at most {} pages per brief".format(MAX_PAGES))
    pages = []
    for u in urls:
        check_public_url(u, resolver)
        if not robots(u):
            if log:
                log({"event": "skipped-robots", "url": u})
            continue
        text = page_text(fetch(u))
        if log:
            log({"event": "fetched", "url": u, "chars": len(text)})
        pages.append({"url": u, "retrieved_at": now(), "text": text})
    return pages


# ---------- guardrail 3: every source cited ----------

def draft_claims(pages):
    claims, seen = [], set()
    for topic, rx in TOPICS:
        for pg in pages:
            for sent in SENT_SPLIT.split(pg["text"]):
                s = sent.strip()
                if not (30 <= len(s) <= 300) or s in seen or "[removed]" in s:
                    continue
                if rx.search(s):
                    seen.add(s)
                    claims.append({"topic": topic, "text": s, "source_url": pg["url"], "retrieved_at": pg["retrieved_at"]})
                    break
            else:
                continue
            break
    return claims[:MAX_CLAIMS]


def verify_claims(claims, pages):
    """Keep only claims whose exact text is in the cited page. Returns (kept, dropped)."""
    by_url = {p["url"]: p["text"] for p in pages}
    kept, dropped = [], []
    for c in claims:
        ok = bool(c.get("source_url")) and c.get("text") and c["text"] in by_url.get(c["source_url"], "")
        (kept if ok else dropped).append(c)
    return kept, dropped


def content_hash(brief):
    body = {k: brief[k] for k in ("company", "claims", "sources")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def build_brief(company, pages):
    kept, dropped = verify_claims(draft_claims(pages), pages)
    brief = {
        "company": company,
        "status": "DRAFT - NOT APPROVED",
        "claims": kept,
        "sources": [{"url": p["url"], "retrieved_at": p["retrieved_at"]} for p in pages],
        "dropped_unverified": len(dropped),
        "approval": None,
    }
    brief["content_hash"] = content_hash(brief)
    return brief


# ---------- guardrail 4: a person approves ----------

def approve(brief, approver, confirm_text):
    if not approver.strip():
        raise RefusedError("approval: an approver name is required")
    if confirm_text.strip() != "APPROVE":
        raise RefusedError("approval: type APPROVE to confirm you reviewed every claim and source")
    if content_hash(brief) != brief["content_hash"]:
        raise RefusedError("approval: the brief was edited after drafting; draft it again")
    brief["status"] = "APPROVED"
    brief["approval"] = {"by": approver.strip(), "at": now(), "content_hash": brief["content_hash"]}
    return brief


def export_markdown(brief):
    ap = brief.get("approval")
    if brief.get("status") != "APPROVED" or not ap:
        raise RefusedError("approval: this brief has not been approved by a person")
    if ap["content_hash"] != content_hash(brief):
        raise RefusedError("approval: the brief changed after it was approved")
    out = ["# Account brief: " + brief["company"], "",
           "Approved by {} on {}. Public sources only. Verify before you use any of it with a customer.".format(ap["by"], ap["at"]), ""]
    n = {}
    for s in brief["sources"]:
        n[s["url"]] = len(n) + 1
    topic = None
    for c in brief["claims"]:
        if c["topic"] != topic:
            topic = c["topic"]
            out += ["## " + topic, ""]
        out.append("- {} [{}]".format(c["text"], n[c["source_url"]]))
    out += ["", "## Sources", ""]
    out += ["{}. {} (retrieved {})".format(n[s["url"]], s["url"], s["retrieved_at"]) for s in brief["sources"]]
    return "\n".join(out) + "\n"


# ---------- command line ----------

def _log_to(path):
    def log(entry):
        entry["at"] = now()
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    return log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft", help="fetch public pages and write a DRAFT brief")
    d.add_argument("--company", required=True)
    d.add_argument("--url", action="append", required=True, help="public https page (repeat, max %d)" % MAX_PAGES)
    d.add_argument("--out", default="brief.json")
    d.add_argument("--audit-log", default="audit.jsonl")
    a = sub.add_parser("approve", help="a person reviews and approves a draft")
    a.add_argument("--brief", default="brief.json")
    a.add_argument("--approver", required=True)
    e = sub.add_parser("export", help="write the approved brief as Markdown")
    e.add_argument("--brief", default="brief.json")
    e.add_argument("--out", default="brief.md")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "draft":
            brief = build_brief(args.company, collect(args.url, log=_log_to(args.audit_log)))
            json.dump(brief, open(args.out, "w"), indent=2)
            print("Draft written to {} with {} cited claims ({} dropped as unverified). Review it, then run approve.".format(args.out, len(brief["claims"]), brief["dropped_unverified"]))
        elif args.cmd == "approve":
            brief = json.load(open(args.brief))
            if not sys.stdin.isatty():
                raise RefusedError("approval: this must be run by a person at a terminal")
            for c in brief["claims"]:
                print("[{}] {}\n    source: {}".format(c["topic"], c["text"], c["source_url"]))
            approve(brief, args.approver, input("\nType APPROVE to confirm you checked each claim against its source: "))
            json.dump(brief, open(args.brief, "w"), indent=2)
            print("Approved by", args.approver)
        else:
            brief = json.load(open(args.brief))
            open(args.out, "w").write(export_markdown(brief))
            print("Wrote", args.out, "- sending it anywhere is your decision, not this tool's.")
    except RefusedError as err:
        print("REFUSED:", err, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
