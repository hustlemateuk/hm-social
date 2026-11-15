# hm-social

Card maker and published card images for Hustle Mate's social posts. Used by Ollie, the scheduled task that creates and schedules posts. Nothing here touches the Ask Hustle Mate app.

## Make cards

```
python3 render.py specs/2026-11-17-vinted.json
```

Writes `cards/<post_id>-1.jpg`, `-2.jpg` and so on: 1080 x 1350 JPEG, accepted by TikTok, Instagram and Facebook. Needs only Pillow (`pip install pillow --break-system-packages` if missing).

If any text does not fit, the script exits with code 2 and names the slide. Shorten the text and run it again. Never ship a card you have not looked at.

After `git push`, each card is public at:

```
https://raw.githubusercontent.com/hustlemateuk/hm-social/main/cards/<post_id>-<n>.jpg
```

## Spec format

One JSON file per post, saved in `specs/`.

```json
{
  "post_id": "2026-11-17-vinted",
  "theme": "mustard",
  "slides": [
    {"type": "cover", "kicker": "Side hustle tax", "title": "Sold on Vinted this year?",
     "sub": "Here's when the app tells HMRC about you.", "badge": "Explained by a Chartered Accountant"},
    {"type": "point", "number": "1", "title": "Selling your own old stuff is usually fine",
     "body": ["Clearing out your wardrobe is not a business.", "Buying to sell on is different."]},
    {"type": "example", "title": "The £1,000 rule uses sales, not profit",
     "rows": [["Sales", "£1,200"], ["Costs", "£500"], ["Profit", "£700"]],
     "result": "Sales are still over £1,000, so you need to tell HMRC.",
     "note": "Assumes you are trading, not selling personal belongings. 2026/27 rules."},
    {"type": "cta", "title": "Got a question like this?",
     "body": ["Ask Hustle Mate.", "Plain English answers, backed by a Chartered Accountant."],
     "button": "Free for 3 days. Link in bio"}
  ]
}
```

- `post_id`: date the post goes out plus a short slug, lower case, hyphens only.
- `theme`: `mustard`, `paper` or `ink`. Use a different theme from the previous post so the grid varies.
- Slide types:
  - `cover`: `title` (required), `kicker`, `sub`, `badge`. Title up to about 8 words.
  - `point`: `title`, `body` (list, one short sentence per item, 2 to 4 items), `number` (optional).
  - `example`: `title`, `rows` (2 to 5 label and value pairs), `result` (the answer, always include it), `note` (assumptions).
  - `cta`: `title`, `body`, `button`, `small` (defaults to "General information, not personal tax advice.").
- A single-image post is one `cover` slide. A carousel is a cover, 2 to 5 middle slides and a `cta`.

## Copy rules

Plain words over jargon ("total sales", not "gross"). One short sentence per line. Show the full worked example including the result. UK English. No em dashes. State assumptions on any tax point. Never personal tax advice.

## Files

- `render.py`: the card maker.
- `fonts/`: Bricolage Grotesque (headings) and Figtree (text), both SIL Open Font Licence.
- `assets/hm-lettering.png`: the real Hustle Mate lettering, placed on the mustard square to form the logo.
- `specs/`: one JSON per post, kept as the record of what was made.
- `cards/`: the rendered images.
- `log.md`: one line per post scheduled (date, networks, topic, source checked).
