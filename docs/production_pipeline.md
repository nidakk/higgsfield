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

## Step 0 — Lock each account's avatar (one-time, per account) — done

Each account needs its own distinct, locked identity before Step 3 can
produce consistent videos. All 5 are locked as of this writing
(`avatar.reference_media_id` in `config/accounts.yaml`); the process for
locking or re-locking one:

1. If a reference photo/video is supplied for that account, bring it in
   with `media_upload_widget` (local file) or `media_import_url` (a
   URL) and use it as a face reference. Otherwise generate from that
   account's `avatar.description` / `hair` / `wardrobe` text via
   `soul_cast` (text-only consistent-character model).
2. Save the resulting media/job ID into that account's
   `avatar.reference_media_id`, and set `avatar.reference_type` to
   `image` or `video` to match.
3. Every video generated for that account from then on (Step 3) must
   pass this same `reference_media_id` as the identity input — never
   let a generation happen without it, or the face will drift and break
   the account's continuity.

### Step 0b — Profile picture per account

A profile picture is a separate asset from the avatar reference —
generate it by conditioning an image-to-image model (`nano_banana_pro`,
role `image`) on the account's **existing approved `reference_media_id`
image job**, asking for a natural/real-feeling backdrop (not a blank
studio background) and describing the setting change only ("same
woman, same face/hair, unchanged — change only the background to ...").
Save the result to `avatar.profile_picture_media_id`.

This only works when `reference_media_id` is itself a completed image
job — passing a video-type reference into an image model fails outright
("Media input not found"). Skincare's `reference_media_id` is a video,
so its profile picture can't be generated this way; the practical
workaround is extracting a still frame from the source video directly
(see the account's config comment for status).

## Step 1 — Generate the daily queue

```
python3 scripts/content_calendar.py --start <date> --days 1
```

This produces one row per post (account, time, hook_type per the weekly
hook schedule, content_type, and a `topic` placeholder). Treat it as the
day's production queue, then fill in `topic` per Step 1.5 before
scripting.

## Step 1.5 — Research today's trending topic per account

Topics are not drawn from a fixed list — each account's 3 daily posts
should cover what's actually being discussed in that niche right now.
For each account, before scripting:

1. Web search using that account's `trend_scope` (`config/accounts.yaml`)
   as the query seed — look for what's currently trending/actively
   discussed in that niche (recent viral posts, hot takes, recurring
   questions, seasonal spikes).
2. Pick 3 distinct angles/topics for that account's day — specific
   enough to hook on (matches the "specific beats general" rule in
   `docs/strategy.md`), not a repeat of a topic covered in the last
   ~1-2 weeks for that account.
3. Fill each row's `topic` field for that account/day with the chosen
   angle before moving to Step 2.

## Step 2 — Script each slot

For each row, write the script using the hook line matching that row's
`hook_type` (pulled from the bank in `docs/hooks_and_scripts.md`) filled
in with that row's `topic` from Step 1.5. Output: a short voiceover
script (~20–25s) plus an on-screen hook line.

## Step 3 — Generate the video

Use `generate_video` with an identity-consistent model — `seedance_2_0`
is the default Higgsfield routes to for identity-preserving generation;
confirm with `models_explore(action: "recommend")` against the goal
("photoreal woman speaking to camera, same identity as a locked
reference") before the first generation per account, since routing can
change.

- Pass that account's `avatar.reference_media_id` (from Step 0) as the
  identity/face reference input — this is what keeps the same woman
  showing up across every video on the account. Use the medias role
  matching that account's `avatar.reference_type`: `image_references`
  for a generated portrait, `video_references` for a user-supplied video
  reference (`seedance_2_0` accepts both directly — no frame extraction
  needed for a video reference).
- `aspect_ratio: "9:16"` (TikTok vertical).
- Use the script from Step 2 as narration; she speaks to camera against
  that account's aesthetic backdrop (`aesthetic` field in
  `config/accounts.yaml`).
- Keep her hair/wardrobe consistent with that account's `avatar` block
  across all of that account's videos, on top of the locked face.
- Pass `get_cost: true` first if credit spend needs to be checked before
  committing to a batch.

## Step 3a — Selfie avatar videos (recurring presence posts)

Distinct from the scripted problem/solution videos in Step 3: a
recurring, unscripted post type where the avatar just holds up her own
phone and smiles at camera — no dialogue, no hook, no script. These
exist to make the account feel like a real person posting, not just a
talking-head content machine. Each account gets 3 of these per day,
same cadence as the scripted posts.

**Locked prompt template** (fill the bracketed parts from that day's
rotation — see below):

> Authentic first-person selfie video, shot entirely from the
> front-facing camera of the phone she is holding — this is her own
> POV, exactly as if she filmed herself. [avatar description], at
> [location], wearing [outfit]. She holds the phone up in one hand at a
> natural selfie distance; her other hand is empty and relaxed. Only
> one phone is ever visible — the one she's holding — there is no
> second phone, no separate camera, and no third-person observer; the
> shot IS her own recording of herself. She looks directly into the
> lens with a warm, natural smile, not speaking, not gesturing — just
> present and smiling, with only subtle natural movement (blinking, a
> soft breath, hair or fabric moving slightly). [location ambience].
> Photoreal, vertical selfie framing, casual handheld selfie energy,
> not a polished studio shot.

**Why the explicit "only one phone / no third-person observer" line is
mandatory:** without it, `seedance_2_0` sometimes renders these as a
third-person shot of her holding a phone — which reads as someone else
filming her while she *also* holds a phone, i.e. two implied cameras.
That's the exact failure mode to avoid; don't drop this line to shorten
the prompt.

- Same identity lock as Step 3 (`avatar.reference_media_id`,
  `image_references` or `video_references` per `reference_type`).
- `aspect_ratio: "9:16"`, `generate_audio: false` (no dialogue).
- Location and outfit come from `scripts/content_calendar.py`'s
  rotation (`selfie_location` / `selfie_outfit` per slot) — it cycles
  through a location/outfit pool so the 3 daily posts per account never
  repeat a setting or outfit on the same day, and the pool keeps
  advancing day over day so it doesn't go stale. Don't hand-author
  these per video; pull them from the calendar row.
- If Higgsfield flags the prompt as matching a preset (e.g. "IN THE
  DARK"), decline it (`declined_preset_id`) and generate literally —
  the presets don't match this format.

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
   `<time>_<topic-slug>_<hook_type>.mp4`, `base64Content` set to the
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
