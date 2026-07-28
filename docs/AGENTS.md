# Agent checklist (releases)

After committing and pushing a **version bump** to `main`:

1. Run `./scripts/release-github.sh` from the repo root (uses `gh` if logged in, else git credentials like `git push`).
2. Do not treat `git push` alone as a complete ship.
3. Update [`REDDIT_RELEASE.md`](REDDIT_RELEASE.md) if the public-facing bullets changed.

See [MAINTENANCE.md](MAINTENANCE.md) → GitHub Release.
