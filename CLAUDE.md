# Operating rules for this repo

TikTok Shop growth content pipeline for a 5-account network. Read
`docs/strategy.md` and `docs/production_pipeline.md` for the full
picture. The rules below are hard constraints, not suggestions — they
exist because breaking them has already cost real money.

## Credit spend

- **Default to the cheapest viable model/resolution for any video
  generation.** For talking/scripted avatar video that means
  `seedance_2_0_mini` at `480p`. Never use the full `seedance_2_0` or a
  higher resolution unless the user explicitly asks for it and accepts
  the cost — don't silently upgrade for quality.
- Always run `get_cost: true` and check `balance` before committing to
  a batch of more than one generation. Tell the user the total cost
  and get confirmation if it's a meaningful spend, especially if the
  balance is low.
- Generate **one test clip** before scaling any new technique or
  prompt pattern to a multi-video batch. Do not assume a fix worked —
  verify it, then scale. Scaling an unverified assumption is what
  turned one mistake into a ~5,100 credit loss on 2026-07-30.

## Scripted/talking avatar video (user-supplied script)

**The script always comes from the user, verbatim — never write,
paraphrase, or "clean up" it.** If no script is supplied, stop and ask
for one; never invent one.

**Mandatory: `docs/scripted_video_pipeline.md`.** Never put a script in
a `generate_video` prompt as a "she says: ..." line and let the model
generate its own matching audio — it improvises the words instead of
reading them, which is exactly what caused the loss above. Instead,
pass the user's script text unchanged as the prompt to `generate_audio`
(model `seed_audio`) to get real TTS audio, then pass that audio job
into `generate_video` as `audio_references` with `generate_audio:
false`. The video model never sees or decides the words.

## Daily default content (no dialogue)

The standing daily post is a **silent** selfie/presence clip — see
`docs/production_pipeline.md`, Step 2. No script, no on-screen text.

## No hooks or captions

This pipeline does not generate on-screen hooks or captions — the user
writes their own. `docs/hooks_and_scripts.md` is archived; don't act on
it.
