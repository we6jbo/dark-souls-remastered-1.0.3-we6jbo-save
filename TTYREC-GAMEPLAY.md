# we6jbo Dark Souls Text/Schematic Gameplay Session

This page accompanies the **we6jbo Dark Souls-inspired text/schematic simulator**
and its ttyrec spectator recordings.

The simulator is not Dark Souls Remastered itself. It uses an original Python/
Tkinter simulation, original narration, simplified combat rules, a schematic
world model, and locally displayed reference maps. No simulator Python source
or third-party map image is automatically committed to this character archive.

## Current simulator

- Simulator version: **124.0**
- Character: **we6jbo**
- Source character archive: `we6jbo-character.json`
- Target cycle: **NG+**
- Intended starting point: **Northern Undead Asylum**
- Manual/automatic control: **manual play with automatic takeover after 2 minutes of inactivity**
- Player interaction immediately returns control from the automatic player.

## Exact archived character build used by the simulator

- Level: **259**
- Souls at archive load/save: **59,713,251**
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

The complete owned inventory, spell collection, equipment collection, quantities,
and recorded upgrade levels remain in `we6jbo-character.json`. Runtime AI context
is mirrored into a local SQLite database outside Git; API keys are never stored there.

## How to create a compatible simulator

This section explains how to make the **text/schematic simulator**, not how the
original game character was created.

You can give ChatGPT a prompt similar to this:

> Create a Python 3 Tkinter Dark Souls-inspired text/schematic simulator that
> reads an existing `we6jbo-character.json` character archive instead of creating
> a new character. Use the archived stats, equipment, spells, covenant and
> inventory as simulator inputs. Model major high-level progression using
> original narration and simplified mechanics rather than copied dialogue,
> artwork, game code, or exact level geometry. Provide manual controls, a
> schematic/local-map view, a replay-friendly terminal spectator feed, and an
> automatic player that takes over after 120 seconds of inactivity and stops as
> soon as the human interacts again. Keep the simulator source and all
> third-party map assets outside the Git repository. Only update the character
> JSON, a small manifest, and this gameplay documentation file.

For an **exact we6jbo build**, use the values listed above and the complete
`we6jbo-character.json` from this repository as the character input.

## Watching ttyrec gameplay

The Tkinter GUI starts `ttyrec` itself in the background. A hidden spectator child receives a terminal-friendly event stream from the GUI, and ttyrec records that stream with timing information. The resulting `.ttyrec` file can be replayed with ttyplay,
Jettyplay, pyttyplay, termplay, asciinema-player, or another compatible player.

The recording itself is intentionally kept outside this character repository by
default. The player can choose where to publish a recording separately.

## Copyright / project separation

The simulator code and third-party map files are intentionally kept out of this
repository. This repository stores the user's character archive, session
metadata, and original documentation. Dark Souls names and other third-party
intellectual property remain the property of their respective rights holders.

## Session status

Last simulator save: **2026-08-20T06:36:36.183506-07:00**

Last session summary:

> Saved we6jbo simulator state at Demon Ruins
