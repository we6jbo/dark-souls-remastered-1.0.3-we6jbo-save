#!/bin/sh
set -eu

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
USER_NAME="we6jbo"
GROUP_NAME="we6jbo"
HOME_DIR="/home/we6jbo"
TARGET="$HOME_DIR/Darksouls-game/KVS6"
CRED_DIR="$HOME_DIR/.w3Whw"
DOC_DIR="$HOME_DIR/.darksouls-character-share-to-github/docs"

if ! id "$USER_NAME" >/dev/null 2>&1; then
    echo "ERROR: user '$USER_NAME' does not exist on this computer." >&2
    exit 1
fi

echo "Verifying package..."
(cd "$SRC_DIR" && md5sum -c fingerprint-file.md5)

mkdir -p "$TARGET/ada" "$CRED_DIR" "$DOC_DIR"

cp "$SRC_DIR/localchat.py" "$TARGET/localchat.py"
cp "$SRC_DIR/STS5.py" "$TARGET/STS5.py"
cp "$SRC_DIR/BBS.py" "$TARGET/BBS.py"
cp "$SRC_DIR/ZU.json" "$TARGET/ZU.json"
cp "$SRC_DIR/localtalk.json" "$TARGET/localtalk.json"
cp "$SRC_DIR/errors.json" "$TARGET/errors.json"
cp "$SRC_DIR/localchat-state.json" "$TARGET/localchat-state.json"
cp "$SRC_DIR/ada-settings.json" "$TARGET/ada-settings.json"
cp "$SRC_DIR/ada/GRp.py" "$TARGET/ada/GRp.py"

# Do not overwrite an existing credentials file.
if [ ! -f "$CRED_DIR/account-info.json" ]; then
    cp "$SRC_DIR/account-info.json" "$CRED_DIR/account-info.json"
    echo
    echo "IMPORTANT: Edit $CRED_DIR/account-info.json and insert your real credentials."
fi

cp "$SRC_DIR/ada-for-localtalk.md" "$DOC_DIR/ada-for-localtalk.md"

chmod 700 "$CRED_DIR"
chmod 600 "$CRED_DIR/account-info.json"
chmod 755 "$TARGET/localchat.py" "$TARGET/BBS.py"
chmod 644 "$TARGET/STS5.py" "$TARGET"/*.json "$TARGET/ada/GRp.py" "$DOC_DIR/ada-for-localtalk.md"

chown -R "$USER_NAME:$GROUP_NAME" "$TARGET" "$CRED_DIR" "$HOME_DIR/.darksouls-character-share-to-github"

python3 -m py_compile "$TARGET/localchat.py" "$TARGET/STS5.py" "$TARGET/BBS.py"

echo
echo "Installed."
echo "Start the GUI with:"
echo "  python3 $TARGET/BBS.py"
