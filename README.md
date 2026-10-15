# AI Ready Reps

A plain-English guide, quiz, and arcade game that teach sales teams to use AI safely.

**Live site:** https://aireadyreps.com

This is a personal portfolio project by [Jared Chapman](https://www.linkedin.com/in/thejaredchapman), built on his own time. The motto is "Reach one, teach one."

> **Talk to your Legal and IT teams before trying any AI tool for work.** This project is general information, not legal advice, and it is not affiliated with any AI vendor.

## What is in it

- AI basics for people who have never used AI at work
- The three kinds of AI help: augmentation, analysis, and automation
- A library of 287 sales use cases rated green (safe), amber (guardrails), or red (not safe)
- A prompt library with 25 copy-ready prompts
- A playbook with worked examples, customer scripts, and a rep FAQ
- Go-to-market guidance for 10 roles, plus a time-saved calculator
- A quiz (10 questions drawn from 17) and an 8-bit sorting game
- A comparison of 8 AI tools, with a page per vendor that lists the vendor's own statements, check dates, and numbered sources
- A safety section covering laws, what to do after a mistake, and AI agents

## For companies

[`ai-ready-reps-company-guide.md`](./ai-ready-reps-company-guide.md) is a Markdown template that companies can adapt into an internal AI acceptable-use and enablement guide. It has fill-in sections for approved tools and contacts, the full use case catalog, the prompt library, vendor notes with sources, and a rollout plan. Have Legal, IT, and Security review any adapted version.

## About the vendor facts

Vendor statements were last checked on **October 14, 2026**. The Vendors tab labels each one:

- **Checked at source:** the vendor's own page was opened and read.
- **Excerpt only:** the vendor's page blocked automated access, so the statement was read from a search excerpt of that page. Confirm it on the page.

Vendor terms change often. Confirm anything that matters in your contract.

## Project structure

| File | Purpose |
|---|---|
| `index.html` | The whole site: HTML, CSS, and JavaScript in one file, with no build step |
| `ai-ready-reps-company-guide.md` | Downloadable company template |
| `LICENSE` | MIT license |

## Run it locally

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

## Deploy

The site is a static page hosted on Vercel and connected to this repository. Every push to `main` deploys to production at https://aireadyreps.com automatically, and other branches get preview deployments.

To deploy by hand from this folder:

```sh
vercel --prod
```

## Contributing and corrections

Found something unclear, outdated, or missing? Open an issue, or message Jared on [LinkedIn](https://www.linkedin.com/in/thejaredchapman). Corrections to vendor facts should include a link to the vendor's page.

## License

[MIT](./LICENSE). If you adapt this work, please keep the attribution.

## Credits

Drafted with the help of an AI assistant (Claude, made by Anthropic), which is one of the vendors covered in the comparison. Content was reviewed by the author.
