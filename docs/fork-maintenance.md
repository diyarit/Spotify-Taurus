# Maintain the Safari-enabled fork

This fork is `diyarit/Spotify-Taurus`. Its upstream is
[the official Taurus project on GitLab](https://gitlab.com/taurustweak/taurus). The Safari extension lives in
`extension/OpenSpotify/`; its packaging hook is in `scripts/pipeline.sh`.
Keep both when resolving future upstream changes.

## Build an IPA in GitHub Actions

1. Open Actions → **Build IPA from your own Spotify IPA** → Run workflow.
2. Supply a direct HTTPS download URL to your own decrypted, supported Spotify IPA.
   Alternatively, save the URL as repository Actions secret `SPOTIFY_IPA_URL` and
   leave the input blank. The secret is optional and is not populated by this change.
3. Leave the upload destination as **artifacts** unless you deliberately want a
   temporary filebin upload. Download `Taurus-Safari-<run number>` from the finished run.
4. Sign the IPA with its embedded extensions retained. Enable Open in Spotify in
   Safari Settings. Actual routing and app behavior still need on-device testing.

The workflow masks the source URL, installs cyan into a virtual environment, runs
Safari tests, builds with `SAFARI=1`, and checks the finished IPA against the source
resources. A stale, absent or wrongly identified extension fails the build. The
source IPA is removed from the runner afterward. No IPA or signing credentials
belong in Git. GitHub artifacts expire after seven days.

The inherited GitHub Release workflow publishes a tweak `.deb`, which cannot contain the
Safari `.appex`. It is therefore disabled by default in forks. Set repository
variable `ENABLE_FORK_RELEASES=true` only after configuring its `SG_FLAG_LIST` secret
and release permissions. Use the IPA workflow for the complete Safari-enabled app.
The inherited in-app updater still follows the upstream author's releases; obtain
new Safari-enabled IPAs from this fork's workflow rather than installing upstream
IPA downloads over this build.

## Sync upstream

**Sync upstream while preserving Safari extension** runs weekly on Monday at
09:23 UTC, or manually from Actions. It:

- Fetches `main` directly from `https://gitlab.com/taurustweak/taurus.git`.
- Merges updates with this fork on `automation/sync-upstream`.
- Pushes that branch and creates or updates one PR targeting this fork's `main`.
- Explicitly dispatches the Safari tests/native extension compilation on the sync
  branch, because pushes made with `GITHUB_TOKEN` do not trigger normal push checks.

Review that PR and the dispatched Safari check before merging. Build an IPA after
merging to verify integration with the full tweak. A conflict aborts the merge and
fails the sync run without pushing that failed merge or changing `main`. There are
no forced resets or forced pushes. Existing extension files survive normal merges;
changes to shared build scripts may need manual resolution.

GitHub Actions must be enabled and allowed to create pull requests in the fork.
The sync job has repository contents, PR and Actions write permissions for its
branch/PR/dispatch operations. The build/check workflows have contents read access.

For a manual local update, start with a clean working tree:

```sh
git switch main
git pull --ff-only origin main
git fetch upstream main
git merge --no-ff upstream/main
make test-safari
# Resolve any conflicts and verify a complete build before pushing main.
git push origin main
```

Avoid `git reset --hard upstream/main` and forced fork-sync commands: those can
replace the fork's custom history. Normal merges retain the extension commits.

GitHub still displays the old GitHub mirror as the fork's network parent. That is
GitHub repository metadata; the authoritative source and synchronization remote
are now GitLab. No history was rewritten or force-pushed. The common ancestor was
`b33f98b`; official GitLab updates through `db59417` were merged, retaining all Safari
commits. A local pre-migration Git bundle is kept in the Desktop workspace's
`backups/` directory.

## Verified setup

On October 19, 2026, the [Safari checks](https://github.com/diyarit/Spotify-Taurus/actions/runs/39294364536) passed in GitHub Actions, including 24 test groups and native extension compilation/signature verification. The [first sync run](https://github.com/diyarit/Spotify-Taurus/actions/runs/39294238343) passed and found no newer upstream changes, so it correctly opened no PR. Local sync tests also verify extension retention and conflict rollback. The full IPA workflow has not been run remotely because no hosted source IPA URL is configured; the full integrated IPA was built and verified locally.

## Official GitLab source correction

On October 19, 2026, the fork merged the seven official GitLab commits through
`db5941761486230f359f2adec7ddae015dc834bc` (Taurus 0.60.2), retaining the Safari source
and packaging hook unchanged. All 24 local test groups, layer checks and workflow
lint passed. The full Taurus 0.60.2 IPA was rebuilt locally and passed archive and
Safari packaging checks. The [corrected sync run](https://github.com/diyarit/Spotify-Taurus/actions/runs/39309105466) fetched GitLab directly and passed with no outstanding upstream changes.

The [GitHub Safari checks](https://github.com/diyarit/Spotify-Taurus/actions/runs/39309106227) also passed against the GitLab-updated source, including all 24 test groups and native extension compilation/signature verification.
