#!/bin/zsh
# One-time: symlink this repo's addon into Anki's addons21 folder.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)/chinese_word_synonyms"
TARGET="${HOME}/Library/Application Support/Anki2/addons21/chinese_word_synonyms"
if [[ -e "$TARGET" && ! -L "$TARGET" ]]; then
  echo "Refusing to overwrite real folder: $TARGET"
  echo "Rename or remove it, then re-run."
  exit 1
fi
rm -f "$TARGET"
ln -s "$SRC" "$TARGET"
echo "Linked:"
ls -la "$TARGET"
