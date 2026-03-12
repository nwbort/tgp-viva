#!/usr/bin/env bash
#
# build-history.sh — Reconstruct a full history CSV from every git commit
# that touched the scraped CSV file, then deduplicate and sort.
#

set -e

CSV_FILE="vivaenergy.com.au-quick-links-terminal-gate-pricing.csv"
HISTORY_FILE="tgp-viva-history.csv"
HEADER="State,City,UnleadedPetrol,PremiumUnleadedPetrol,UnleadedPetrol E10,UnleadedPetrol 98,Diesel,BiodieselB5,Date"
TMP_FILE=$(mktemp)

# Collect data rows from every commit that touched the CSV
git log --format='%H' --all -- "$CSV_FILE" | while read -r sha; do
  # Extract the CSV at that commit, skip the header line
  git show "${sha}:${CSV_FILE}" 2>/dev/null | tail -n +2
done > "$TMP_FILE"

# Write header, then deduplicate and sort (by Date descending, then State, City)
{
  echo "$HEADER"
  sort -u -t, -k9,9r -k1,1 -k2,2 "$TMP_FILE"
} > "$HISTORY_FILE"

rm -f "$TMP_FILE"

ROWS=$(tail -n +2 "$HISTORY_FILE" | wc -l)
echo "Built $HISTORY_FILE with $ROWS data rows"
