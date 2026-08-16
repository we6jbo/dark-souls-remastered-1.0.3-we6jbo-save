# Local Talk + BBS Debian Installation

This bundle installs the headless Local Talk IRC backend and the two-tab BBS GUI.

## What you will see

After installation, run:

```bash
python3 /home/we6jbo/Darksouls-game/KVS6/BBS.py
```

The BBS window has:

1. **Messages** — static message: `From: Sysop To: Everyone Body: Welcome to the BBS.`
2. **Local Talk** — `[Start talking]` / `[Stop talking]`, a message entry field, and Send.

`BBS.py` starts `localchat.py` automatically. `localchat.py` has no GUI. It listens only on `127.0.0.1:32512`. When BBS.py closes normally it asks localchat.py to shut down.

## Install

Copy this entire folder to the Debian computer, then run:

```bash
cd /path/to/localtalk-complete
chmod +x install-localchat.sh
./install-localchat.sh
```

The installer places the project in:

```text
/home/we6jbo/Darksouls-game/KVS6/
```

Credentials live separately at:

```text
/home/we6jbo/.w3Whw/account-info.json
```

Open that JSON file and replace the placeholder values with the credentials you want Local Talk to use.

## Diagnostics

Current state:

```text
/home/we6jbo/Darksouls-game/KVS6/localchat-state.json
```

Errors and health/event history:

```text
/home/we6jbo/Darksouls-game/KVS6/errors.json
```

Last 11 human-looking IRC messages:

```text
/home/we6jbo/Darksouls-game/KVS6/localtalk.json
```

ADA settings:

```text
/home/we6jbo/Darksouls-game/KVS6/ada-settings.json
```

ADA plugins:

```text
/home/we6jbo/Darksouls-game/KVS6/ada/
```

## Verify files

From the bundle directory:

```bash
md5sum -c fingerprint-file.md5
```

## Project reference

https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/
