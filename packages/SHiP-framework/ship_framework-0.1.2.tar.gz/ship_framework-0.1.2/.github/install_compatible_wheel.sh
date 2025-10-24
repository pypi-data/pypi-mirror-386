#!/usr/bin/env bash
set -euo pipefail

# Directory containing your wheel files
DIST_DIR="../dist"

# Ensure dist/ exists
if [[ ! -d "$DIST_DIR" ]]; then
  echo "Error: Directory '$DIST_DIR' not found." >&2
  exit 1
fi

# Iterate through each .whl file
for whl in "$DIST_DIR"/*.whl; do
  # Skip if no files match
  [[ -e "$whl" ]] || { echo "No .whl files in $DIST_DIR"; exit 1; }

  echo -n "Checking compatibility of $(basename "$whl")… "

  # Dry-run install
  if pip install --dry-run "$whl" >/dev/null 2>&1; then
    echo "compatible ✅"
    echo "Installing $(basename "$whl")…"
    pip install "$whl"
    echo "Done."
    exit 0
  else
    echo "incompatible ❌"
  fi
done

echo "No compatible wheel found in '$DIST_DIR'." >&2
exit 1
