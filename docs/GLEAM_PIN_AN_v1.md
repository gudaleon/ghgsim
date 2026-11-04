# GLEAM pin (AN_v1)

Checked 2026-11-03 (America/Toronto) with `git ls-remote`, the GitHub REST API and the r-universe API.

| What | SHA | Date (UTC) | Evidence |
|---|---|---|---|
| Tag `v0.8.0-alpha` (lightweight tag, no tag object) | `b0937d260ea8c8022c241275220709c9294bae5f` (`b0937d2`) | commit 2026-03-22 22:36; GitHub release published 2026-03-23 02:17 | `git ls-remote https://github.com/un-fao/GLEAM refs/tags/v0.8.0*`; `GET /repos/un-fao/GLEAM/git/refs/tags/v0.8.0-alpha` -> object type `commit` |
| r-universe build of `gleam` 0.8.0 | `90e416197e89093c4f3a347b263ba805d33d4aac` (`90e4161`) | 2026-05-14 15:43 ("CRAN Readiness - Few last improvements", PR #168) | `https://un-fao.r-universe.dev/api/packages/gleam` -> `RemoteSha` |

`90e4161` is 38 commits ahead of `b0937d2` on `main` (GitHub compare API, behind_by 0). Both carry
`Version: 0.8.0` in `DESCRIPTION`, so the version number alone does not identify the code.

**Pin used by ghgsim:** the release tag, `v0.8.0-alpha` = commit `b0937d2`. This is what
`data/upstream_sources_AN_v1.json` already records. The earlier note (DECISIONS_AN_v3 item 7) that the tag is
`90e4161` was wrong: `90e4161` is the r-universe build of `main`, not the tag. If GLEAM is installed from
r-universe instead of the tag, record `RemoteSha` from `packageDescription("gleam")` and cite that SHA, not the tag.

Licence: AGPL-3. Run unmodified on Bubble as an outside model; no GLEAM code enters ghgsim.
