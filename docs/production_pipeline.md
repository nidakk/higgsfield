# Production Pipeline

How a calendar slot from `scripts/content_calendar.py` becomes a published
TikTok post, using the Higgsfield tools available in this workspace. This
is an operating runbook, not a standalone script — steps that call
Higgsfield (`generate_video`, `virality_predictor`, `tiktok_*`) run through
an agent session with those tools connected, since they aren't a public
API a local script can call directly.

## Step 0 — Connect the 5 TikTok accounts (one-time, per account)

Current state: **0 accounts connected** (`tiktok_accounts` returns empty).
Before any publishing can happen:

1. Create the 5 TikTok accounts (moms / skincare / self-care / hair /
   home) if they don't exist yet.
2. For each, run `tiktok_connect` and complete the OAuth flow.
3. Run `tiktok_accounts` to confirm each shows `status: active`, and
   record its `connector_id` into the matching entry's `connector_id`
   field in `config/accounts.yaml`. Also fill in `handle`.
4. Re-run `tiktok_connect` → `tiktok_reconnect` for any account that
   later shows `status: error`.

Nothing downstream works without this step.

## Step 1 — Generate the daily queue

```
python3 scripts/content_calendar.py --start <date> --days 1
```

This produces one row per post (account, time, pillar, hook_type,
content_type). Treat it as the day's production queue.

## Step 2 — Script each slot

For each row, write the script using the matching template in
`docs/hooks_and_scripts.md` for that niche + hook_type. Output: a short
voiceover script (~20–25s) plus an on-screen hook line.

## Step 3 — Generate the faceless video

Use the `faceless-video` Higgsfield workflow (narrator-led, non-photoreal,
reusable style/character/location assets) — call
`get_workflow_instructions(workflow="faceless-video")` for the full
SKILL.md before the first generation per account, since it defines how to
lock a consistent visual identity per channel.

For the generation call itself:

- `generate_video` with `aspect_ratio: "9:16"` (TikTok vertical — the
  workflow defaults to 16:9, override explicitly).
- Use the script from Step 2 as the narration/prompt input.
- Keep the same locked style/background aesthetic per account (see the
  `aesthetic` field in `config/accounts.yaml`) across all of that
  account's videos — this is what makes an account recognizable without
  a face.
- Pass `get_cost: true` first if credit spend needs to be checked before
  committing to a batch.

## Step 4 — Local format validation

Before spending a publish attempt, validate the exported file with the
existing checker:

```
python3 scripts/tiktok_analysis.py path/to/video.mp4
```

Confirms vertical orientation, resolution, and duration are within
TikTok's publishing requirements. Fix and re-export on any `FAIL`.

## Step 5 — Virality gate

Run `virality_predictor` (`action: "create"`) on the generated video
before publishing. Use the dashboard's hook-strength and retention-risk
signals as a go/no-go gate:

- Strong hook + low retention risk → proceed to publish.
- Weak hook or high retention risk → revise the script's hook/tension
  beats (Step 2) and regenerate rather than posting a video likely to
  underperform. Protecting the account's growth-phase momentum matters
  more than hitting the 3x/day quota on a specific day.

## Step 6 — Publish

Two-step Higgsfield flow, per account (`connector_id` from
`config/accounts.yaml`):

1. `tiktok_prepare_publish` — `mode: "DIRECT_POST"`, `media_type: "VIDEO"`,
   the Higgsfield-hosted `video_url`, `video_duration_sec`, caption in
   `title`/`description`. Returns required confirmations and privacy
   options.
2. `tiktok_publish` — pass `publish_session_id` from step 1, set every
   flag from `required_confirmations` to `true`, and **set `is_aigc:
   true`** (all content here is AI-generated — this disclosure is
   mandatory, not optional). Set `privacy_level: "PUBLIC_TO_EVERYONE"`
   for growth-phase posts.

Then `tiktok_publish_status` to confirm it went live, and mark that
calendar row's `status` as `posted` (manually, or extend
`content_calendar.py`'s output if this becomes high-volume enough to
warrant a status-tracking store).

## Phase 2 (shop-primed) additions

Once an account's `phase` in `config/accounts.yaml` flips to
`shop_primed` (crossed 5,000 followers — see `docs/strategy.md`), the
calendar generator starts marking ~30% of slots `shop_adjacent`. For
those slots:

- Script still opens with the same hook/tension structure — the payoff
  becomes "here's what I actually use," not a hard sell.
- Attach TikTok Shop product tagging at publish time (once Shop is
  live on the account) rather than changing the video pipeline itself.
- Watch the KPIs in `docs/strategy.md` weekly; dial the ratio back via
  `phase2_sell_ratio` in the config if engagement drops.
