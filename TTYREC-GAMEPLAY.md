# we6jbo Dark Souls Text/Schematic Gameplay Session

This page accompanies the **we6jbo Dark Souls-inspired text/schematic simulator**
and its ttyrec spectator recordings.

The simulator is not Dark Souls Remastered itself. It uses an original Python/
Tkinter simulation, original narration, simplified combat rules, a schematic
world model, and locally displayed reference maps. No simulator Python source
or third-party map image is automatically committed to this character archive.

## Current simulator

- Simulator version: **4.0**
- Character: **we6jbo**
- Source character archive: `we6jbo-character.json`
- Target cycle: **NG+**
- Intended starting point: **Northern Undead Asylum**
- Manual/automatic control: manual play with automatic takeover after **2 minutes** of inactivity
- Any player keyboard or mouse interaction immediately returns control.

## Exact archived character build used by the simulator

- Level: **259**
- Souls: **398,300**
- Humanity counter: **0**
- Covenant: **Chaos Servant +2**
- Vitality: **50**
- Attunement: **50**
- Endurance: **53**
- Strength: **16**
- Dexterity: **45**
- Resistance: **30**
- Intelligence: **58**
- Faith: **38**

### Equipped snapshot

- Right hand 1: **Moonlight Greatsword +5**
- Right hand 2: **Logan's Catalyst**
- Left hand 1: **Balder Shield +12**
- Left hand 2: **Pyromancy Flame +5**
- Head: **Crown of Dusk**
- Chest: **Witch Cloak +5**
- Hands: **Brass Gauntlets +5**
- Legs: **Xanthous Waistcloth +5**
- Ring 1: **Bellowing Dragoncrest Ring**
- Ring 2: **Havel's Ring**

The complete inventory, spell collection, equipment collection, quantities, and
recorded upgrades live in `we6jbo-character.json`.

## How to make the simulator

This describes the simulator, not how the original character was created.

Ask ChatGPT:

> Create a Python 3 Tkinter Dark Souls-inspired text/schematic simulator that
> reads an existing `we6jbo-character.json` character archive instead of creating
> a new character. Use the archived stats, equipment, spells, covenant and
> inventory as simulator inputs. Model major high-level progression with
> original narration and simplified mechanics rather than copied dialogue,
> artwork, game code, or exact level geometry. Include a replay-friendly
> terminal spectator feed suitable for ttyrec. Let a local automatic player
> take over after 120 seconds of inactivity and immediately stop when the human
> interacts again. Keep simulator source and third-party map assets outside the
> Git repository. Update only the character JSON, session manifest, and this
> documentation file.

For the exact **we6jbo** build, use this repository's `we6jbo-character.json`.

## Watching a ttyrec recording

Run the simulator under `ttyrec`. The Tkinter GUI remains the interactive player
view while the launching terminal becomes the spectator feed. That feed includes
the countdown, pre-show, area travel, encounters, boss objectives, deaths,
automatic-player takeovers, human-control returns, saves, and GitHub guide link.

The `.ttyrec` recording is kept outside this character repository by default, under `/home/we6jbo/Darksouls-game/ttyrecs/`.
It can be replayed with ttyplay, Jettyplay, pyttyplay, termplay, asciinema-player,
or another ttyrec-compatible player.

## Project separation

The simulator Python source and third-party map images are intentionally kept
outside this Git repository. This repository contains the character archive,
small session metadata, and original explanatory documentation.


## Local runtime layout

The recommended runtime layout is:

```text
/home/we6jbo/Darksouls-game/
├── dark-souls-we6jbo-simulator.py
├── record-we6jbo-ttyrec.sh
├── maps/
├── cache/
│   └── maps/
└── ttyrecs/
```

The character archive remains separate at:

```text
/home/we6jbo/.darksouls-character-share-to-github/
```

The simulator refuses to run from inside that Git repository.
