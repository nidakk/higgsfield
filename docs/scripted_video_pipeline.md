# Scripted talking-avatar video pipeline (word-accurate, low-cost)

For any video where the avatar speaks a script the user wrote (not the
silent no-dialogue selfie default in `docs/production_pipeline.md`, Step
2) — e.g. a one-off recreation, a multi-video campaign. This doc exists
because of a real, expensive failure (2026-07-30): `generate_video` was
called with the script embedded in the prompt as `She says: "..."` and
`generate_audio: true`, on the assumption the model would read it back
verbatim. It doesn't — the model *improvises* both the video and the
speech together from the prompt as a creative cue, not a script it
reads. That produced wrong/substituted words repeatedly, and got
"fixed" by adding stronger wording to the prompt ("verbatim, word for
word") and re-running full batches — twice — without ever testing
whether that actually worked. It didn't reliably. Something like
~5,100 credits were spent this way before the root cause was found.
**Do not repeat that pattern: don't scale a batch on an unverified
assumption about how a tool works.**

## Mandatory procedure

**1. Cost floor by default.** Use `seedance_2_0_mini` (not the full
`seedance_2_0`) and `480p` resolution unless the user explicitly asks
for higher quality and accepts the cost tradeoff. Mini + 480p is the
cheapest combination that still supports identity reference +
audio-driven generation. Never silently upgrade model/resolution to
improve quality — ask first, same as any other credit-spend decision.

**2. Audio-first, not prompt-described dialogue.** Never put the
script in the video prompt as something the avatar "says" and let
`generate_video` invent matching audio. Instead:

   a. Generate the exact script as real text-to-speech first, via
      `generate_audio` (model `seed_audio`), using the script text
      verbatim as the prompt. This is deterministic TTS — it reads the
      literal text, it does not improvise — so word accuracy is
      structural, not a matter of prompt wording.
   b. Pass the resulting audio job ID into `generate_video`'s `medias`
      as `role: "audio_references"`, alongside the avatar's identity
      reference (`image_references`/`video_references` per that
      account's `reference_type`).
   c. Set `generate_audio: false` on the `generate_video` call — the
      spoken track comes from the TTS step, not from the video model.
      The video prompt should describe performance/energy/setting only
      (pacing, gesture, wardrobe, location), never repeat the script
      text as a "she says" line.

**3. One test clip before any batch.** Before generating more than one
clip this way, generate exactly one, and get the user's explicit
confirmation the words are correct before running the rest. Do not
scale a multi-video batch on an assumption that the fix worked —
that's the mistake that caused the original waste.

**4. `get_cost: true` preflight** on both the `generate_audio` and
`generate_video` calls before committing to a batch, and confirm the
total against current balance (`balance`) — don't discover a shortfall
mid-batch.

**5. Long-script splitting still applies.** Scripts over ~35-40 words
still need to be split into two ≤15s segments and stitched via
`explainer_video` (duration cap is 15s regardless of model). Generate
each segment's TTS audio from that segment's own exact text — don't
generate one long audio track and try to split it.

**6. Continuity constraints stay in the video prompt**, since those are
about performance/visuals, not text accuracy: one hand always holding
the phone, only the other hand free to gesture, natural brisk pacing
(not slow, not frantic). These are legitimately prompt-controllable —
only the *words* need to come from TTS, not the performance direction.

## Why this fixes the root cause, not just the symptom

The word-accuracy failure was never a wording problem — it was an
architecture problem: the video model was the one deciding what to
say. Feeding it pre-generated TTS audio as a reference removes that
decision from the video model entirely. A stronger prompt instruction
("verbatim, word for word") cannot fix that, because the model was
never reading the script in the first place — this was tried twice and
didn't reliably work.
