# Open in Spotify for Taurus

The Taurus build now includes a Safari web extension, built from source in
`extension/OpenSpotify`. It opens standard Spotify URIs, so it does not depend on
EeveeSpotify's `spotify://eevee/...` URL handler. `make build`, `make release`, and
`make install` include it by default. Use `SAFARI=0` or the pipeline's `--no-safari`
option to exclude it.

## Build and enable

1. Install full Xcode and select its developer directory. Follow Taurus's existing
   README for Theos, iPhoneOS 26+ SDK, cyan, and the other build dependencies.
2. Put your own decrypted Spotify IPA (the version supported by Taurus) in `ipa/`.
3. Run `make test-safari`, then `make release`. The output is
   `out/Taurus-<mod version>.ipa`.
4. Sign and sideload the output with a signer that retains and signs embedded
   extensions. The extension must have its own valid signature/provisioning and a
   bundle ID prefixed by the final host app ID. Some sideloaders offer a switch to
   remove extensions; leave that off. This adds one more extension App ID, in addition
   to the Live Activity and any original Spotify extensions retained by the signer.
5. On the iPhone, open Settings → Apps → Safari → Extensions → Open in Spotify
   (older iOS: Settings → Safari → Extensions). Enable it and allow it on the listed
   Spotify websites. If it is absent, check that the signer retained the `.appex`.
6. Open a supported Spotify URL in Safari. The extension tries once to open the app
   and shows an **Open in Spotify** link for cases where Safari requires a tap.
   Safari controls its own confirmation prompt; the extension cannot remove it.

The Safari toolbar popup can turn automatic opening off. Manual links still work.
**Dismiss** hides the fallback for the current destination. Existing tabs may need
reloading after the extension is first enabled or its website permissions change.

To build just the extension with Xcode, without compiling the Taurus tweak:

```sh
bash scripts/build-safari-extension.sh /path/to/Spotify.app/Info.plist out/safari-extension
```

That produces `out/safari-extension/TaurusOpenSpotify.appex`, ad-hoc signed for
packaging. It is not an independently installable iPhone app. The normal pipeline
passes it to cyan alongside the existing Live Activity extension. Final IPA signing
is still necessary. `BUNDLE_ID=your.host.id` sets the generated extension ID's prefix;
a signer changing the host ID later must update/provision embedded extension IDs too.
The extension's bundle versions are taken from the host Info.plist.

## Coverage

| URL or scenario | Behavior |
| --- | --- |
| Track, album, artist, playlist, podcast show/episode, audiobook | Validates the 22-character Spotify content ID and opens its standard URI |
| `intl-xx` / `intl-xx-XX` and `/embed/` prefixes | Normalizes the prefixes |
| Legacy `/user/name/playlist/id` links | Opens the playlist |
| User profiles, genres, selected collections | Opens the corresponding URI |
| `/search/text` and `/search?q=text` | Encodes the search query |
| Track/episode/audiobook `t=` | Retains recognized playback positions; actual seeking depends on Spotify |
| `spotify.link`, `spotify.app.link`, `spoti.fi` | Uses recognized destination query fields or canonical/app-link metadata; otherwise waits for the provider's HTTP redirect |
| Spotify's web player changes URLs without a page reload | Checks the current URL every 750 ms while visible and on browser navigation/visibility events |
| Automatic launch is blocked or cancelled | Leaves the manual link; does not continuously retry |
| Immediate reload / Back | Session storage suppresses a repeat for 30 seconds; each URI is attempted at most once per document, up to a bounded recent history |
| Unknown, login, payment, homepage, malformed or unrelated URLs | Leaves the page alone |

Permissions cover only the five Spotify link hosts, local preference storage, and
the active tab for the toolbar popup. No all-websites access, telemetry, account
credentials, background service worker, or remote link-resolution service is used.
The content script runs in the top frame only. It does not intercept modified clicks,
downloads, page actions, or links before Safari reaches a permitted Spotify host.

## Limits and verification

“Everything” has practical limits: this extension runs in Safari on permitted hosts.
It cannot intercept links inside another app's embedded browser, repair a dead or
geoblocked short link, or force Spotify to support an unknown URI. Opaque short
links without usable metadata depend on the link provider's redirect. If official
Spotify is installed alongside Taurus and both register `spotify:`, iOS chooses the
handler; standard URIs cannot guarantee which copy opens. Browser protections may
require a deliberate tap. Permissions must be granted for each relevant hostname.

Verified locally on October 19, 2026:

- `make test-safari`: 19 JavaScript test groups and three Python packaging tests passed.
- `bash scripts/check-layers.sh` and `git diff --check` passed.
- Browser smoke tests passed in headless Google Chrome using mocked extension APIs:
  320px/375px phones, landscape and tablet layouts; dismissal; history changes;
  replacement of page content; keyboard focus; popup preference saving; light/dark
  appearance. Screenshots are under `out/safari-browser-check/`.

The supplied Spotify 9.1.90 IPA has now passed archive CRC checks. Its main binary
reports `cryptid: 0`, and its Info.plist registers `spotify:`. A fingerprint is in
`out/input-verification.json`; the original IPA is unchanged. Local Theos and cyan
tooling are prepared under `out/`. Full Xcode 27.1 is installed and initialized.
The native Safari extension compiled and passed `codesign --verify --strict` before
packaging. The full pipeline successfully built Taurus 0.60.1 on Spotify 9.1.90,
including the Safari and Live Activity extensions, App Group shim, alternate icons
and merged App Intents metadata.

The final `../Taurus-0.60.1-Safari.ipa` (131.2 MiB) passed archive CRC checks and
contains matching host/extension identities and versions, byte-identical Safari
resources, the native arm64 handler, and the expected injected libraries. See
`out/final-package-verification.json` and `out/desktop-build.log` for evidence.
Production signing, device installation, actual Safari extension activation, and
Spotify routing have **not** been verified. No device installation was attempted,
as requested. The independent
`.github/workflows/test-safari.yml` builds and verifies the extension on an Xcode
runner without needing a Spotify IPA. [GitHub verification passed](https://github.com/diyarit/Spotify-Taurus/actions/runs/39294364536) on October 19, 2026, including all 24 routing/lifecycle/packaging/sync test groups and native extension compilation.

The browser smoke test is optional:

```sh
python3 -m venv /tmp/taurus-safari-tests
/tmp/taurus-safari-tests/bin/pip install playwright
/tmp/taurus-safari-tests/bin/python tests/open-spotify/browser_check.py
```

It uses installed Google Chrome, fixtures and mocked extension APIs. It does not
load an actual Safari extension.

On-device acceptance: use the native look on iOS 16.1+ or the redesigned look on
iOS 26+, enable the Safari extension, and test a track, album, playlist, episode,
localized URL, embed URL and short link. Cancel one app-launch prompt, return from
Spotify, navigate within Spotify's web player, and reload: there should be no prompt
loop. Disable automatic opening and check that the visible link still opens the
right content. Confirm the Live Activity and normal Taurus features still work.

## Source references

- Authoritative Taurus source: https://gitlab.com/taurustweak/taurus at `db5941761486230f359f2adec7ddae015dc834bc` (Taurus 0.60.2).
- The initial GitHub copy at `b33f98b` shares the same history. Its newer GitLab commits were merged while retaining the Safari extension.
- Requested extension reference: https://github.com/BillyCurtis/OpenSpotifySafariExtension at `6523fcd3a45796beb89ce82f3f9ba032c85ae837`.
  The sibling clone is kept intact. Its compiled executable, images, and JavaScript
  have not been bundled into Taurus; the routing and native shell here are new source.
- Spotify URI format: https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids
- Safari permissions: https://developer.apple.com/documentation/safariservices/managing-safari-web-extension-permissions

## Fork workflow

See [fork maintenance](fork-maintenance.md) for building this integration in GitHub Actions and merging upstream updates while retaining it. The finished IPA is checked by `scripts/check-safari-ipa.py`; run it locally with the IPA path to check packaging.
