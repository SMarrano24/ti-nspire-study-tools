#!/bin/bash
# Double-click me. Pick documents, and I'll make TI-Nspire-sized images of them.
cd "$(dirname "$0")"

# First run: set up a private Python with the two libraries this needs.
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c "import fitz, PIL" 2>/dev/null; then
  echo "First-time setup (about a minute)..."
  rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q pymupdf pillow || exit 1
fi

FILES=$(osascript -e 'set fs to choose file with prompt "Choose documents to convert for your TI-Nspire" with multiple selections allowed
set out to ""
repeat with f in fs
  set out to out & POSIX path of f & linefeed
end repeat
return out') || exit 0

MODE=$(osascript -e 'choose from list {"Big text (best for reading)", "Original look (diagrams, math)"} with prompt "How should it look?" default items {"Big text (best for reading)"}')
[ "$MODE" = "false" ] && exit 0
case "$MODE" in Original*) MODE=page ;; *) MODE=reflow ;; esac

LAST=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  .venv/bin/python nspire_convert.py --mode "$MODE" "$f"
  LAST="$f"
done <<< "$FILES"

# Show the folder of images for the last document.
STEM=$(basename "${LAST%.*}" | sed -E 's/[^A-Za-z0-9]+/_/g; s/^_+|_+$//g' | cut -c1-20)
open "$(dirname "$LAST")/${STEM}_nspire" 2>/dev/null
echo "Done. You can close this window."
