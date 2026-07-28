# Production Pipeline

How a calendar slot from `scripts/content_calendar.py` becomes a finished,
delivered video, using the Higgsfield and Google Drive tools available in
this workspace. This is an operating runbook, not a standalone script —
steps that call Higgsfield (`generate_video`, `virality_predictor`) or
Google Drive (`create_file`) run through an agent session with those
tools connected, since they aren't a public API a local script can call
directly.

**Current delivery target: Google Drive, not TikTok.** Each day's batch
is generated, quality-checked, and dropped into Drive for review —
nothing auto-publishes to TikTok. Connecting the 5 TikTok accounts and
turning on direct publishing is a deliberate later step (Step 7), done
once you're ready to start actually posting.

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

## Step 6 — Deliver to Google Drive

Once a video passes Steps 4–5, upload it (and its caption) to Drive
instead of publishing:

1. Folder structure, created once and reused:
   ```
   TikTok Shop Growth/
     Moms/2026-07-28/
     Skincare/2026-07-28/
     Self-care/2026-07-28/
     Hair/2026-07-28/
     Home/2026-07-28/
   ```
   Create the root folder and one subfolder per account with
   `create_file` (`mimeType: "application/vnd.google-apps.folder"`),
   record the returned folder IDs in `config/accounts.yaml`
   (`drive_folder_id` per account) so later uploads target them by
   `parentId` instead of re-creating folders. Create a fresh
   date subfolder under each account folder at the start of each day's
   batch.
2. Upload the video with `create_file`: `title` using the convention
   `<time>_<pillar-slug>_<hook_type>.mp4`, `base64Content` set to the
   file's contents, `contentMimeType: "video/mp4"`,
   `disableConversionToGoogleType: true` (video has no Google-native
   equivalent, but set it explicitly so nothing gets reprocessed), and
   `parentId` set to that day's account/date folder.
3. Upload the matching script/caption as a sidecar text file in the same
   folder (`title` matching the video minus extension, `.txt`,
   `textContent` = script + caption + hashtags) so whoever reviews the
   batch has the full context next to the video.
4. Mark that calendar row's `status` as `delivered` (manually, or extend
   `content_calendar.py`'s output if this becomes high-volume enough to
   warrant a status-tracking store).

## Step 7 — Later: connect TikTok and publish (deferred)

Not part of the current daily workflow — do this only when you're ready
to start actually posting to TikTok:

1. Create the 5 TikTok accounts (moms / skincare / self-care / hair /
   home) if they don't exist yet.
2. For each, run `tiktok_connect` and complete the OAuth flow.
3. Run `tiktok_accounts` to confirm each shows `status: active`, and
   record its `connector_id` into the matching entry's `connector_id`
   field in `config/accounts.yaml`. Also fill in `handle`.
4. For each Drive video you're ready to post: `tiktok_prepare_publish`
   (`mode: "DIRECT_POST"`, `media_type: "VIDEO"`, a Higgsfield-hosted
   `video_url` — re-upload/import the Drive file to Higgsfield first,
   since TikTok requires a verified Higgsfield-hosted source domain,
   `video_duration_sec`, caption in `title`/`description`), then
   `tiktok_publish` with every `required_confirmations` flag set `true`
   and **`is_aigc: true`** (mandatory — all content here is
   AI-generated). Then `tiktok_publish_status` to confirm it went live.

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
