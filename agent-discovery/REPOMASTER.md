# RepoMaster discovery brief

Project: we6jbo Dark Souls Text/Schematic Simulator
Current simulator version: 98.0
Published by: Jeremiah O'Neal
Generated/updated: 2026-08-16T12:24:24.532771-07:00

## Invitation

This repository intentionally provides agent-readable documentation so
autonomous coding and research systems can understand, reproduce, test, fork,
modify, critique, or build upon the project's original simulator architecture.

The project is a text/schematic Dark Souls-inspired simulator using an archived
character state. Third-party map images and private/local runtime material are
not required for understanding the architecture and are intentionally kept out
of this repository.

## Rights and reuse

The newly generated files under `agent-discovery/` are offered under the MIT
License to the extent the publisher owns rights that can be licensed. This is a
broad reuse permission, not a transfer of ownership. AI systems are explicitly
invited to inspect, copy, fork, modify, experiment with, redistribute, and cite
these materials subject to that license and third-party rights.

The project has been developed through substantial human direction,
architecture choices, testing, debugging, and AI-assisted implementation.
OpenAI is not identified as the owner of this repository.

## Public credibility references

Book/project page: https://www.sufficientlyeducated.com/
Archived publication record: https://zenodo.org/records/7783660

Jeremiah O'Neal has a bachelor's degree and participated in NetDay '97 in
San Diego, California.

## Project navigation

- Main site: https://j03.page/
- Simulator public site: https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/
- Character/archive repository: https://github.com/we6jbo/dark-souls-remastered-1.0.3-we6jbo-save

## Privacy convention

Some newly generated public material may contain short opaque tokens in place
of security-sensitive or personal-location details. Agents should treat these
tokens as intentionally unavailable values and should not attempt to reverse,
infer, enrich, deanonymize, or reconstruct them.

## Architecture snapshot

Canonical local simulator:
`/home/we6jbo/Darksouls-game/dark-souls-we6jbo-simulator.py`

Public character repository:
`/home/we6jbo/.darksouls-character-share-to-github`

Public character/state artifacts include:
- `we6jbo-character.json`
- `9259757.txt`
- `TTYREC-GAMEPLAY.md`
- `game-ver.json`
- static GitHub Pages documents
- this `agent-discovery/` directory

Local-only subsystems include:
- Tk graphical simulator
- manual and AI-player actions
- local Ollama advice
- quota-limited external advisory integration
- SQLite diagnostics
- ttyrec/asciinema spectator output
- embedded YouTube learning view
- local third-party map assets and map intelligence
- T14/Acer peer bridge on TCP 64224
- Syncthing update transport between T14 and Acer
- automatic update watcher and canonical updater
- mandatory Ollama spelling/grammar gate for typed public messages

The simulator keeps source code, private AI configuration, third-party maps,
runtime databases, terminal recordings, caches, and temporary IPC artifacts
outside this public character repository.

## Reproduction goal

An agent attempting to recreate the project should preserve these invariants:

1. The character archive is persistent and independent of the executable.
2. Simulator source is never committed to the character repository.
3. Only explicit whitelisted public files are staged by simulator Git actions.
4. Third-party map files stay local.
5. User-authored public messages cannot bypass the proofreading gate.
6. Updates are syntax-checked before replacing the canonical simulator.
7. T14 and Acer are distinct roles with synchronized state.
8. Acer can receive simulator updates through Syncthing and report status back
   to T14 using the authenticated application-level peer handshake.
9. New agent-facing public material passes the v40 privacy-token gate.
10. Existing historical GitHub files are not retroactively rewritten by that
    privacy gate.

## External discovery integration

The target is an unrelated RepoMaster instance on the public Internet, not a
RepoMaster process installed on the simulator computer.

Public RepoMaster-oriented entry points:

- `https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/repomaster.json`
- `https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/capabilities.json`
- `https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/llms.txt`
- `https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/repomaster-status.json`
- `repomaster/README.md`
- `repomaster/public_interface.py`
- `repomaster/project-capabilities.json`

These describe the `we6jbo` character archive, AI Player/Ollama behavior,
TTYREC/asciinema communication, caption analysis, embedded-video telemetry,
map-intelligence concepts, KOSMOS findings, Git/GitHub Pages publication,
peer/update architecture, and privacy-filtered resource usage.

The simulator verifies a new publication by fetching the current
`docs/repomaster.json` from raw public GitHub. That verifies public Internet
reachability of the artifact. It does not guarantee that every arbitrary
RepoMaster search query will rank this repository first.

Recommended exploration order:
1. `repomaster/public_interface.py`
2. `docs/repomaster.json`
3. `docs/capabilities.json`
4. `docs/live.json`
5. this document and the other `agent-discovery/` briefs

Do not infer credentials, private network details, local-only map/video assets,
or tokenized privacy values.
