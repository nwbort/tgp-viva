#!/bin/bash
./download.sh 'https://www.vivaenergy.com.au/quick-links/terminal-gate-pricing'

# Append new rows to the history file, deduplicating as we go
CSV_FILE="vivaenergy.com.au-quick-links-terminal-gate-pricing.csv"
HISTORY_FILE="tgp-viva-history.csv"
HEADER="State,City,UnleadedPetrol,PremiumUnleadedPetrol,UnleadedPetrol E10,UnleadedPetrol 98,Diesel,BiodieselB5,Date"

if [ ! -f "$HISTORY_FILE" ]; then
  echo "$HEADER" > "$HISTORY_FILE"
fi

# Merge existing history (minus header) with new data (minus header), deduplicate, sort
TMP_FILE=$(mktemp)
{ tail -n +2 "$HISTORY_FILE"; tail -n +2 "$CSV_FILE"; } | sort -u -t, -k9,9r -k1,1 -k2,2 > "$TMP_FILE"
{ echo "$HEADER"; cat "$TMP_FILE"; } > "$HISTORY_FILE"
rm -f "$TMP_FILE"

# Regenerate normalised CSV and JSON from the full history
python3 normalise.py
