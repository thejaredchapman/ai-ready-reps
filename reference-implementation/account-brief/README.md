# Account Brief: a reference implementation

The AI Ready Reps guide rates "draft an account brief from public information" as an **amber** use case: allowed with guardrails. This is a small working tool that follows those guardrails, so the rules are code you can read and test instead of a policy document.

It is a teaching example, not a product. It uses only the Python standard library and calls no AI model.

## The four guardrails, and where each one lives

| Guardrail | What the code does | Tests |
|---|---|---|
| **Public data only** | https only; no logins, credentials, odd ports, or internal hostnames; refuses hosts that resolve to private addresses; obeys `robots.txt`; strips emails and phone numbers | `PublicOnly` |
| **Read-only research** | The only network function is `http_get`, which sends a GET with no cookies or auth. There is no CRM, email, or write code to call. Max 5 pages, 1 MB each | `PublicOnly`, `ReadOnly` |
| **Every source cited** | Each claim is a verbatim sentence plus its URL and retrieval time. `verify_claims` re-reads the page and drops any claim it cannot find, so a made-up or uncited claim never reaches the brief | `Cited` |
| **A person approves** | A brief starts as `DRAFT - NOT APPROVED`. `approve` needs a terminal, an approver name, and the typed word `APPROVE`. The approval is tied to a hash of the content, so any edit afterward blocks export. Nothing is ever sent | `Approval` |

Every page fetch is appended to `audit.jsonl`.

## Run it

```sh
cd reference-implementation/account-brief
python3 -m unittest -v                       # 14 tests, no network needed

python3 account_brief.py draft --company "Example Co" \
  --url https://www.example.com/about --url https://www.example.com/news
python3 account_brief.py approve --approver "Your Name"   # you read every claim, then type APPROVE
python3 account_brief.py export                           # writes brief.md, only after approval
```

## What it deliberately does not do

- It does not write the outreach email, update the CRM, or send anything. Those are the steps where the guide says a human decides. See the Advanced tab for when an agent should earn write access.
- It does not summarize in its own words. It quotes sentences, so it finds fewer facts than a language model would. That is the trade: a thin brief you can fully check beats a rich brief you cannot.
- Its sentence picker is simple keyword matching. Expect gaps, and read the source pages for anything that matters.

## Adding a model later

You can replace `draft_claims` with a call to any AI model. Keep `verify_claims` between the model and the brief: it rejects any claim whose exact text is not on the cited page. If you want the model to paraphrase, change the check to require a quoted passage from the page alongside each paraphrase, and keep the human approval step.

## License

MIT, same as the rest of the repository.
