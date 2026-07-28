# TikTok Shop Growth Strategy — 5-Account Faceless Network

## Goal

Grow five faceless, aesthetic-background TikTok accounts to 5,000 followers
each, then pivot each account's content mix toward TikTok Shop–ready
selling content, without losing the audience that got them there.

| # | Niche       | Core audience problem the account solves |
|---|-------------|---------------------------------------------------------------|
| 1 | Moms        | Overwhelm, guilt, lack of time, conflicting parenting advice |
| 2 | Skincare    | Confusing routines, product overwhelm, results that don't match promises |
| 3 | Self-care   | Burnout, no time for self, guilt around rest |
| 4 | Hair        | Damage, frizz, styling that doesn't hold, product overwhelm |
| 5 | Home        | Clutter, chores that never end, spaces that don't feel calm |

## Two-phase arc

**Phase 1 — Growth (0 → 5,000 followers).** Every post's only job is to earn
a follow. Content is purely problem/solution: name a daily pain point in the
niche, then give advice so specific and relatable the viewer can't scroll
past it. No selling, no product pushes, no shop links. The account is
building trust and a correctly-targeted audience — followers who have the
exact problem the eventual TikTok Shop products solve.

**Phase 2 — Shop-primed (5,000+ followers).** Once an account crosses 5,000
followers, shift the mix to roughly 70% problem/solution (unchanged, keeps
growth compounding) and 30% shop-adjacent: product-in-use demos, "what
actually worked for me" content, and shoppable posts. Never flip 100% to
selling — the account's growth engine is the trust content, and killing it
kills future reach. Track engagement rate weekly after the switch; if it
drops more than ~20% relative to the pre-switch baseline, dial the sell
ratio back down.

Phase transition is per-account, not simultaneous — each of the five hits
5,000 on its own timeline.

## Posting cadence

- 3 posts/day/account × 5 accounts = 15 posts/day total.
- Stagger post times per account rather than posting all five
  simultaneously — spread load on scripting/filming/editing and avoid
  looking like a bot network.
- Consistency beats burst posting for TikTok's algorithm — a missed day
  costs more than an extra post gains. Build the pipeline (see
  `docs/production_pipeline.md`) assuming a standing daily queue, not
  one-off bursts.

## Format: faceless, aesthetic-background

- No face on camera, ever — build channel identity through the same
  advice angle and same visual/aesthetic world (color palette, motion
  style, backgrounds/b-roll) so it's recognizable without ever showing a
  face.
- Backgrounds: niche-appropriate aesthetic footage/motion — calm,
  scroll-stopping, on-brand for the niche (e.g. Home = tidy sunlit
  interiors; Skincare = macro texture/product shots; Moms = soft
  lifestyle scenes). Use the `faceless-video` Higgsfield workflow
  (non-photoreal, narrator-led) or narrator-over-b-roll depending on the
  niche's best-performing look — test both early and standardize on
  whichever holds retention better per account.
- Voiceover or on-screen text carries the advice; the visual is
  atmosphere, not the message.

## The retention mechanic: "can't scroll away"

The stated goal is *weirdly constant engagement* — tension that holds the
viewer, not just a good opener. Structure every script the same way
(templates in `docs/hooks_and_scripts.md`):

1. **Hook (0–2s):** name the exact problem or a pattern-interrupt claim
   ("Nobody tells you this about—"). Specific beats general — "why your
   towel is ruining your skin" beats "skincare tips."
2. **Tension (2–6s):** widen the gap — why the obvious fix doesn't work,
   why they've been doing it wrong, what's quietly making it worse. This
   is the "open loop" that keeps them watching for the resolution.
3. **Relatable proof (6–12s):** one concrete, specific, personal-feeling
   detail that makes the advice feel earned, not generic — a number, a
   timeframe, a "the moment I realized."
4. **Payoff / advice (12–20s):** the actual fix, stated plainly and
   usably — something they can act on today.
5. **Soft loop-close / CTA (last 2s):** a reason to follow ("part 2
   tomorrow"), comment (ask a polarizing-but-safe question), or save
   (frame the advice as reference-worthy).

Avoid a resolved, tidy ending on every single post — occasionally end on
a cliffhanger or "comment X and I'll send you the rest" to intentionally
manufacture the sense that scrolling away means missing something.

## KPIs to track per account

- Follower count (primary gate at 5,000)
- Average watch-through / retention (proxy for hook + tension strength)
- Saves and shares (proxy for "advice was worth keeping" — the strongest
  TikTok Shop-readiness signal, since it means the audience trusts the
  advice enough to act on it)
- Comment rate and comment sentiment (audience-fit signal — are commenters
  the actual target buyer for the niche?)
- Post-Phase-2: click-through / add-to-cart rate on shop-tagged posts

## Risks and guardrails

- Don't cross-promote the five accounts to each other overtly — TikTok
  and viewers both penalize obvious network behavior; let the aesthetic
  and advice angle do the differentiation instead.
- Keep AIGC/faceless disclosure compliant with TikTok's policies when
  publishing (see `docs/production_pipeline.md` — `is_aigc` flag is
  mandatory on every publish call).
- Quality-gate every video with Virality Predictor before publishing
  (see pipeline doc) rather than posting blind — protects both the pace
  and the trust the growth phase depends on.
