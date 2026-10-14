# YouTube platform facts (verified against official docs on 2026-10-14)

Each item was checked on support.google.com/youtube or developers.google.com/youtube. Re-verify before relying on these, because the platform changes.

## Multi-language audio
- **Access:** requires "Advanced features" and may be limited to a subset of creators. Desktop YouTube Studio only. See https://support.google.com/youtube/answer/13338784 and https://support.google.com/youtube/answer/9890437
- **Steps:** Studio → **Languages** → video → **Add language** → next to **Dub** click **Add** → select the audio file → **Publish**.
- **File requirements:** the file must be "roughly the same length as your video" in a supported audio-only format. The help page does **not** state exact formats, the length tolerance, or stereo/mono and sample-rate rules. This studio exports exact-length 48 kHz stereo WAV plus AAC `.m4a` to stay safe.
- **Automatic dubbing** exists and is on by default for eligible creators. Delete the auto-dub for a language before uploading your own track. See https://support.google.com/youtube/answer/15569972
- **No API upload:** the Data API v3 has **no endpoint to upload or attach audio tracks**. The only related fields are `snippet.defaultAudioLanguage` and the read-only `fileDetails.audioStreams`. See https://developers.google.com/youtube/v3/docs and the revision history. This studio never uploads.
- **Localized title and description:** use `videos.localizations` (BCP-47 keys), or in Studio go to Subtitles/Languages → Title & description. See https://support.google.com/youtube/answer/6289575
- **Captions:** use `captions.insert` (400 quota units, `youtube.force-ssl` scope, ≤ 100 MB), or in Studio go to Subtitles → Upload file → With timing. See https://support.google.com/youtube/answer/2734796

## YouTube Analytics API v2
- **`ageGroup`:** `age13-17, age18-24, age25-34, age35-44, age45-54, age55-64, age65-`. There is **no 50+ bucket**.
  - Track "55+" as `age55-64` plus `age65-`.
  - Report `age45-54` separately, because it straddles 50.
  - Since 2026-03-09 the buckets include viewers YouTube estimates to be under 18.
- **`gender`:** female, male, user_specified.
- **`creatorContentType`:** LIVE_STREAM, SHORTS, STORY, VIDEO_ON_DEMAND, UNSPECIFIED. Use it to split Shorts from long-form.
- **Retention:** `elapsedVideoTimeRatio` has 100 points (0.01–1.0), with `audienceWatchRatio` and `relativeRetentionPerformance`.
- **Revenue:**
  - Metrics: `estimatedRevenue`, `estimatedAdRevenue`, `playbackBasedCpm`, `cpm`.
  - They need the `yt-analytics-monetary.readonly` scope and Partner Program membership. Otherwise the API returns 403.
- **Impressions and CTR:** not available in the Analytics API. They are only in the bulk Reporting API (`channel_reach_basic_a1`, metrics `video_thumbnail_impressions`, `video_thumbnail_impressions_ctr`).
- **Returning, new and unique viewers:** not available in the API (Studio UI only).
- **Privacy thresholds:** demographic thresholds are unpublished. Missing data means "withheld", not zero.
- **Scopes:** `yt-analytics.readonly` and `yt-analytics-monetary.readonly`.

## RPM vs CPM
- **RPM:** what the creator earns per 1,000 views, after revenue share, from all revenue sources.
- **CPM:** what advertisers pay per 1,000 ad impressions, before revenue share.
- Source: https://support.google.com/youtube/answer/9314357
- Never infer another channel's RPM from its public view counts.

## Shorts
- Up to **3 minutes**, square or vertical. See https://support.google.com/youtube/answer/15424877
- **Related video:** requires Advanced features. Set it in YouTube Studio → Content → (Short) → Related video → Save. The target must be your own public or unlisted video. See https://support.google.com/youtube/answer/14075157

## Advertiser-friendly guidelines: war and violence
These are summarised from https://support.google.com/youtube/answer/6162278
- **Full ads:** non-graphic, educational coverage of war.
- **Limited ads:** raw conflict footage without educational context.
- **No ads, in any context:** graphic war injury or death.
- Graphic content in the thumbnail or the first 7 seconds hurts monetization.

## AI and synthetic content disclosure
Disclosure is required when:
- a real person appears to say or do something they didn't,
- real footage is altered,
- a realistic scene that didn't happen is generated, or
- AI music is the main focus.

Set it in Studio → Attributes → "AI use", or in the API as `status.containsSyntheticMedia`. See https://support.google.com/youtube/answer/14328491

Our stylised animated recreations are labelled on screen as illustrative. Review the policy for any realistic-looking synthetic imagery.

## Not confirmed
- Exact accepted audio formats and length tolerance for dub uploads.
- The current Studio menu label ("Languages" vs "Subtitles").
- Whether multi-language audio access is limited beyond Advanced features.
