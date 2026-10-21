[Guide](../README.md) · [简体中文](../zh-CN/development.md)

# Development and releases

## Development

The repository declares its development toolchain in `mise.toml`. With [mise](https://mise.jdx.dev) installed, `mise install` provisions the pinned Python and Node versions, and the same file exposes the common commands as tasks:

```bash
mise run install      # create .venv and install the editable package with dev dependencies
mise run test         # install dev dependencies and run pytest
mise run cli -- --v   # run the CLI from this checkout
mise run regression
mise run smoke
mise run parity
mise run check
```

The Python tasks share the editable `.venv` checkout, including regression and smoke. `mise run python path/to/script.py` runs additional development scripts in that environment. The pinned Python 3.13 satisfies the supported version range; CI independently tests Python 3.10/3.12. mise is optional: the `npm` scripts below remain supported and CI keeps using `actions/setup-python` and `actions/setup-node`.

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m smart_search.cli regression
.\.venv\Scripts\python.exe -m smart_search.cli smoke --mock --format json
npm test
npm pack --dry-run
```

## Release lanes

Stable releases use Git tags and npm `latest`:

```powershell
git tag vX.Y.Z
git push origin vX.Y.Z
```

Test releases use npm prereleases and do not move `latest`. A push to `main` publishes the next `<package.json version>-beta.N` version under npm dist-tag `next`; `N` resets for each stable base version. Before creating a beta, the workflow compares the current stable `package.json` version with its first parent, so a merge or squash release bump skips the beta and the matching `vX.Y.Z` tag publishes npm `latest`. The `chore(release): bump version to X.Y.Z` title remains a legacy fallback. For example, after `0.1.10-beta.1` and `0.1.10-beta.2`, the next `main` publish is `0.1.10-beta.3`.

GitHub Actions also supports manual backfill for historical test builds through `workflow_dispatch`. Use an explicit `target_ref` plus an exact version such as `0.1.9-beta.1`, and publish it with a non-`latest` tag such as `backfill`. npm versions are immutable: old `*-dev.*` packages cannot be renamed in place, only superseded by new `*-beta.N` packages and optionally deprecated later with npm owner credentials.

Stable GitHub releases read optional body text from `.github/releases/vX.Y.Z.md` and append npm package, dist-tag, and workflow-run metadata automatically. Add that file before tagging a stable version so the GitHub Release page explains what changed instead of only listing package metadata.

The read-only `CI` workflow runs on pull requests, pushes to `main`, and manual dispatch. It verifies Ubuntu Node 18/Python 3.10, Ubuntu Node 24/Python 3.12, and Windows Node 22/Python 3.12 without publishing. Its package gate checks public/package skill parity, packs a real tarball, installs it under a fresh temporary npm prefix, and runs version, packaged regression, and mock smoke there.

Release closeout checklist:

1. Verify the registry and tags before changing anything: `npm view @konbakuyomu/smart-search versions --json`, `npm view @konbakuyomu/smart-search dist-tags --json`, and `gh release list --repo konbakuyomu/smartsearch --limit 100`.
2. For historical beta backfill, publish the replacement `*-beta.N` package through Actions with `create_github_release=false` if the workflow token cannot create releases, then create the missing GitHub prerelease locally with `gh release create vX.Y.Z-beta.N --target <commit> --prerelease --latest=false`.
3. Treat npm `E409` during parallel backfills as a registry concurrency failure, not a version-design failure. Re-run the affected version serially after checking whether the package already exists.
4. Do a machine-readable gap check: expected beta versions minus npm versions must be empty, and expected `v*beta*` releases minus GitHub prereleases must be empty.
5. Install the selected test build explicitly, for example `mise use -g "npm:@konbakuyomu/smart-search@0.1.10-beta.3" -y --pin`, then run `mise reshim`, `where.exe smart-search`, `smart-search --version`, `smart-search regression`, `smart-search smoke --mock --format json`, and a non-ASCII JSON pipe such as `smart-search deep "深度搜索一下最近的比特币行情" --format json | ConvertFrom-Json`.

## Historical release note

### v0.1.14 (historical)

This stable patch release moves the tested `0.1.13-beta.4` CLI and bundled skill contract into npm `latest`.

- Fixes GitHub issue #7: npm `latest` now includes the `smart-search skills` command expected by the newer installed `smart-search-cli` skill.
- `smart-search skills status` reports whether installed user-level skills are missing, stale, up to date, or contain extra files without writing anything.
- `smart-search skills update` refreshes only the managed bundled `smart-search-cli` files for selected AI-tool targets after a CLI upgrade.
- `smart-search diagnose openai-compatible --format markdown` produces a focused, copy-pasteable troubleshooting report for OpenAI-compatible search hangs/timeouts.
- Docs/API routing now prefers Context7 for library/framework documentation and keeps Exa for official domains, papers, product pages, and trusted-site discovery.
- README, bundled skill assets, release notes, and tests now document and verify the exact stable package behavior.

## Refresh the references

After changing commands, help text or config metadata, run the following in the development environment and review both languages.

```sh
python scripts/generate_references.py
python -m pytest tests/test_guide.py
```
