# 90-day pilot kit

A small, honest way to test whether AI Ready Reps changes what reps know and do. Run it with **3 to 5 reps**. With a group that small, report the raw numbers and the reps' own words, not percentages or claims about "impact".

> **Status:** No pilot has been run yet. This folder is the plan and the tools. Results will be added to `RESULTS.md` only when real reps have supplied them.

Before you start, get approval from Legal and IT, and tell the reps that taking part is voluntary and that their scores are used only for this pilot. Do not collect customer data.

## What you measure

| Measure | How | When |
|---|---|---|
| Quiz score before | Rep takes the site quiz and writes down the score | Day 0 |
| Quiz score after | Same, a fresh draw of questions | Day 90 |
| Green use cases tried | Rep logs each green use case they actually used, from the Use cases tab | Ongoing |
| Rule slips | Any time a rep nearly broke a red or amber rule and caught it | Ongoing |
| Rep's note | One sentence: what saved time, what did not | Days 30, 60, 90 |

The quiz draws 10 questions at random from a bank, so the before and after quizzes will not be identical. That is useful, because it stops reps from memorizing answers. It also means a one-point change is noise.

## The 90 days

- **Days 0 to 7. Baseline.** Reps take the quiz cold and record the score. Walk them through the traffic-light rule. Confirm which AI tool the company has approved.
- **Days 8 to 30. Green only.** Each rep picks 3 green use cases from the Use cases tab and tries them on real work, in the approved tool. Log each one in the tracker.
- **Days 31 to 60. Add one amber.** With a manager's sign-off and the listed control, each rep tries one amber use case. Hold a 30-minute review: what worked, what nearly went wrong.
- **Days 61 to 90. Advanced.** Read the Advanced tab together. Decide which rung of the permission ladder each workflow sits on and whether any should move up. Retake the quiz. Collect the final notes.

## Files

- `tracker-template.csv`: one row per rep per event. Copy it, fill it in, never commit real names.
- `summarize.py`: reads the tracker and prints quiz scores before and after, green use cases tried, and slips. Run `python3 summarize.py my-tracker.csv`.
- `test_summarize.py`: tests for the summary script. Run `python3 -m unittest`.

Use rep codes such as `R1` to `R5`, not names.

## Reporting

Report what happened, including what did not work. Example wording: "Four reps took part. Quiz scores went from 5, 6, 7, 6 to 8, 7, 9, 8. Together they tried 11 different green use cases. Two reported a near-miss they caught." Do not write that AI "improved performance" unless you measured performance.
