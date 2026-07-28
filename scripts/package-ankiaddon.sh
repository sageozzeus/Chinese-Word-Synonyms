#!/bin/zsh
# Build chinese_word_synonyms-VERSION.ankiaddon from package contents.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION=$(python3 -c "from chinese_word_synonyms.about_meta import ADDON_VERSION; print(ADDON_VERSION)")
OUT="chinese_word_synonyms-${VERSION}.ankiaddon"
rm -f "$OUT"
(
  cd chinese_word_synonyms
  zip -r "../$OUT" . \
    -x '__pycache__/*' '*/__pycache__/*' '*.pyc' 'meta.json' '.DS_Store' '*/.DS_Store'
)
echo "Built $OUT"
unzip -l "$OUT" | head -n 20
