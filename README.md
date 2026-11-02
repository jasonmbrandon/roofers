# Your Favorite Roofing — demo template

A one-page marketing site for a **fictional** roofing company. Static HTML, CSS
and two JavaScript files: no framework, no build step, no dependencies. Every
image is drawn in SVG, so it ships with no photography at all.

It exists to show what a premium roofing site looks like before a real client's
words and photos are anywhere near it. Read the *Placeholders* section before it
goes in front of anyone.

## Run it

From this folder:

```sh
python -m http.server 4380 --bind 127.0.0.1
```

Then open <http://127.0.0.1:4380/>. Every asset and page link is relative, so the
same files work at a domain root, in a subfolder (a GitHub Pages project site,
for example) and on any static host. Opening `index.html` straight off disk is
the one case that still wants a server: browsers block the external `<use>`
reference to the icon sprite over `file://`, so the icons disappear.

No Python? Any static file server will do — `npx serve .`, `npx http-server`,
or the tiny one this build was previewed with, which lives one level up in the
workspace tooling folder:

```sh
node ../.tools/serve.mjs "$PWD" 4380
```

## Deploy

Static, no build step. On GitHub Pages: **Settings → Pages → Deploy from a
branch → `main` / `/ (root)`**, which serves this folder at
`https://<user>.github.io/roofers/` — the relative links mean that subpath works
with no changes. Netlify, Vercel and Cloudflare Pages all take the repo directly
with an empty build command and `/` as the output directory.

The only thing a host needs to leave alone is the file names: `index.html` at the
root, everything else under `assets/`.

## The page, top to bottom

| Section | What it does |
| --- | --- |
| Hero (`#top`) | Shingled roof plane, gutter and vent at dusk; headline, two calls to action, and a "book a visit" card pinned over the roof |
| Roof anatomy (`#anatomy`) | Cut-away diagram with eight numbered layers. Click a chip *or* a row in the list: the layer lights up, the rest dim, the copy changes |
| How it's built (`#build`) | Pinned 340vh scene. Four passes tear the old roof off, roll the underlayment, lay nine courses of shingles and close the ridge as you scroll |
| Services (`#services`) | Six job types with their own icons and three deliverables each |
| Before & after (`#work`) | Draggable roof-surface slider: worn tabs, moss and algae against a new roof and clean gutter |
| Process (`#process`) | Five steps with a copper rail that fills as you scroll |
| Promises | Four commitments in a dark band |
| Questions (`#faq`) | Seven native `<details>` answers, one open by default |
| Free inspection (`#quote`) | Form: name, phone, optional email, address/ZIP, job type, message |
| Footer | Brand, section links, contact, and the demo notice |

## The motion layer

Two files, both optional: drop the `<link>` and `<script>` pair and the page is
a still, complete site — every state that the scripts paint is also the state
the page loads in.

- **`assets/motion.js`** — one `requestAnimationFrame` loop for everything
  scroll-driven: a reading-progress hairline, hero parallax, the build scene,
  the process rail, and staggered section reveals through IntersectionObserver.
- **`assets/motion.css`** — the pre-paint states for all of it, every rule gated
  on `html.js` so nothing can be left invisible if the script never runs.

**The build scene.** `index.html` ships the plane, deck boards, felt, old roof,
flashings, ridge cap and badge; `motion.js` generates the nine shingle courses
as SVG groups. Scroll passes drive:

| Scroll | Stage | What happens |
| --- | --- | --- |
| 0 – 0.17 | 01 Strip & inspect | The old roof slides away and fades |
| 0.15 – 0.41 | 02 Deck & membrane | Underlayment unrolls left to right, then its seams appear |
| 0.36 – 0.44 | 03 Shingles & flashing | Edge metal appears |
| 0.44 – 0.90 | 03 Shingles & flashing | Nine courses drop in from the eave up, 30px slide each |
| 0.885 – 0.96 | 04 Ridge & clear-up | Ridge cap settles onto the peak |

Below 980px the section stops being pinned: the art sits above the steps and
the stage follows whichever step is on screen, because a 340vh scroll scene on
a phone is a trap.

**Reduced motion.** `prefers-reduced-motion: reduce` skips every effect. The
build scene paints its finished state instead of animating, reveals are shown,
and the progress hairline is removed.

## Interactions

- **Anatomy:** the list is a real tablist (arrow keys work); the numbered chips
  on the diagram are a second, pointer-style way in. Both drive the same state.
- **Before/after:** drag anywhere on the image, or focus the handle and use
  ←/→ (hold Shift for bigger steps), Home and End. The clip and the handle are
  driven by one `--split` custom property.
- **Navigation:** anchors, an active-section highlight, and a full-screen menu
  under 980px that closes on Escape, on a link, or on resize.
- **Form:** browser-side validation with a specific message per problem, a
  honeypot that quietly accepts bots, and an inline status line.

## The form

Out of the box it **sends nothing**. It validates, then composes an email to
`hello@yourfavoriteroofing.example` in the visitor's mail app and shows an
inline confirmation. That is honest for a demo and needs no account.

To collect submissions server-side, add one attribute to the form in
`index.html`:

```html
<form class="quote-form" data-quote-form data-endpoint="https://…">
```

With `data-endpoint` set, the script POSTs the fields as JSON, expects a 2xx,
and reports success or a call-us fallback. Anything that accepts JSON works:
Formspree, Basin, a Cloudflare Worker. Nothing is wired yet — that is a
decision for whoever buys the template, and it should get an approval before
anything is sent.

## Brand

| Token | Value | Used for |
| --- | --- | --- |
| `--ink` | `#0F151B` | Hero, build scene, before/after, quote, footer |
| `--ink-2` | `#141C23` | Promises band |
| `--paper` | `#F4F0E8` | Anatomy, services, process, FAQ |
| `--copper` | `#C97545` | Buttons, the second line of every heading, diagram chips |
| `--slate` | `#2C363F` | Shingle fills, secondary marks |

Headings are **Roboto Slab**, body and UI are **Montserrat** — both
self-hosted, variable, and copied from `../lgrtile/assets/fonts/` (the same two
files every spec site in this repo uses). Emphasis inside a heading is a weight
change and a colour, never italics: the Roboto Slab variable file has no italic
axis, and a synthesised slant is not the look.

## Placeholders — read before showing this to anyone

Nothing on the page is a fabricated statistic. There are no project counts,
years in business, star ratings, review quotes or prices anywhere, because none
of those exist for a company that does not exist. Everything else is a
placeholder that must be replaced:

| Where | Placeholder | Replace with |
| --- | --- | --- |
| Header, hero card, quote, footer, sticky bar | `(555) 010-0199` and `tel:+15550100199` | The real number — it appears in five `tel:` links |
| Quote section, footer | `hello@yourfavoriteroofing.example` | The real inbox, and in `assets/site.js` (`EMAIL`) for the mailto fallback |
| Hero card, quote, footer | "Your city and the towns around it" | The real service towns, ideally as a list (and in the schema, if you add one) |
| Footer | The demo notice | Delete it once the real business is behind the page |
| `<head>` | No canonical, no `og:url`, no `og:image`, no JSON-LD | Add them with the real domain, a 1200×630 card, and a `RoofingContractor` schema — but only real details (no `aggregateRating` until there are real reviews) |

Claims that are written as service promises rather than facts — free
inspection, itemised estimate, workmanship warranty, daily clean-up — are
deliberately unquantified. If the real business cannot honour one, delete it
rather than soften it; and confirm the insurance and licence wording with them
before launch, since the built page makes no such claim and customers will ask.

## If a real client takes this over

1. Swap the phone, email, service area and demo notice (table above).
2. Add their real photos. The illustrations are placeholders with a job: the
   hero, the before/after and the build scene each assume a dark, cool palette,
   so warm daylight photos need their own section rather than these slots.
3. Point the form at an endpoint and test one submission end to end.
4. Add GA4 and mark the form submission as a conversion (`site.js` already
   composes the mailto, so hook the click, or add the event where the fetch
   succeeds).
5. Get the warranty terms, insurance certificate and licence number in writing
   before any of it is mentioned on the page.

## Files

```text
index.html              the whole page
assets/styles.css       base styles, layout, components, responsive rules
assets/motion.css       pre-paint states for the scroll effects
assets/motion.js        scroll effects + the generated shingle courses
assets/site.js          nav, anatomy, slider, form, scrollspy
assets/sprite.svg       UI icons (phone, arrow, check, plus, mail, pin, clock)
assets/favicon.svg      roof mark
assets/fonts/           Roboto Slab + Montserrat, variable woff2
```
