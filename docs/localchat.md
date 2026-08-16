# Local Talk IRC Backend and BBS GUI

Local Talk is the headless IRC backend used by the BBS GUI in this project. It provides a local-only control interface for `BBS.py`, manages IRC connections and channel rotation, records recent human-looking chat activity, and exposes `[Start talking]` / `[Stop talking]` status information to the BBS Local Talk tab.

## Get the Local Talk files

The project files are stored in the `localchat` directory of this repository:

https://github.com/we6jbo/dark-souls-remastered-1.0.3-we6jbo-save/tree/main/localchat

On a new Debian computer, clone or download the repository and enter the Local Talk directory.

Example:

```bash
git clone https://github.com/we6jbo/dark-souls-remastered-1.0.3-we6jbo-save.git
cd dark-souls-remastered-1.0.3-we6jbo-save/localchat
```

## Verify the files

The directory includes `fingerprint-file.md5`.

Run:

```bash
md5sum -c fingerprint-file.md5
```

The bundled project files should report `OK`.

The repository contains a **blank credential template** named:

```text
account-info.json
```

Real passwords and email credentials must not be committed to GitHub.

On the maintainer's systems, the private credential file is stored at:

```text
~/.actualcredsfile
```

For installation, copy that private file to the runtime credential location:

```bash
mkdir -p ~/.w3Whw
cp ~/.actualcredsfile ~/.w3Whw/account-info.json
chmod 700 ~/.w3Whw
chmod 600 ~/.w3Whw/account-info.json
```

If `~/.actualcredsfile` does not exist on a new machine, create `~/.w3Whw/account-info.json` from the blank `account-info.json` template and fill in the credentials locally.

**Never commit the real credential file.**

## Install

Run:

```bash
chmod +x install-localchat.sh
./install-localchat.sh
```

The installer places the working project under:

```text
/home/we6jbo/Darksouls-game/KVS6/
```

The runtime credential file is:

```text
/home/we6jbo/.w3Whw/account-info.json
```

After installation, start the BBS GUI with:

```bash
python3 /home/we6jbo/Darksouls-game/KVS6/BBS.py
```

## BBS interface

`BBS.py` provides two tabs:

### Messages

The Messages tab initially displays:

```text
From: Sysop
To: Everyone
Body: Welcome to the BBS.
```

### Local Talk

The Local Talk tab connects to the headless `localchat.py` backend.

The backend listens only on:

```text
127.0.0.1:32512
```

It is not intended to listen on the LAN or public Internet.

The Local Talk tab displays:

```text
[Start talking]
```

or:

```text
[Stop talking]
```

and provides a message entry field and Send button.

`BBS.py` starts `localchat.py` when the BBS starts and asks it to shut down when the BBS closes normally.

## Runtime and diagnostic files

Current Local Talk state:

```text
/home/we6jbo/Darksouls-game/KVS6/localchat-state.json
```

Diagnostic and error history:

```text
/home/we6jbo/Darksouls-game/KVS6/errors.json
```

The last 11 human-looking IRC messages:

```text
/home/we6jbo/Darksouls-game/KVS6/localtalk.json
```

ADA/accessibility settings:

```text
/home/we6jbo/Darksouls-game/KVS6/ada-settings.json
```

ADA plugin directory:

```text
/home/we6jbo/Darksouls-game/KVS6/ada/
```

## ADA Local Talk plugins

ADA Local Talk plugins can extend accessibility behavior without putting IRC logic into the BBS GUI. See:

```text
localchat/ada-for-localtalk.md
```

for plugin details.

## Security

The GitHub repository must contain only the blank `account-info.json` template.

The real credential file belongs outside the repository at:

```text
~/.actualcredsfile
```

and the runtime copy belongs at:

```text
~/.w3Whw/account-info.json
```

Both should be readable only by the owning user.

## Related Dark Souls project

https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/
