#!/usr/bin/env bash
#
# download - Downloader that extracts tables from HTML pages as CSV
# Usage: ./download.sh URL

set -e

if [ $# -ne 1 ]; then
  echo "Usage: $0 URL"
  exit 1
fi

URL="$1"

if [[ ! "$URL" =~ ^https?:// ]]; then
  echo "Error: URL must start with http:// or https://"
  exit 1
fi

TEMP_FILE=$(mktemp)

echo "Downloading $URL"
curl -s -L "$URL" -o "$TEMP_FILE" || {
  echo "Error: Failed to download $URL"
  rm -f "$TEMP_FILE"
  exit 1
}

MIME_TYPE=$(file --mime-type -b "$TEMP_FILE")
FILENAME=$(echo "$URL" | sed -E 's|^https?://||' | sed -E 's|^www\.||' | sed 's|/$||' | sed 's|/|-|g')

if [[ "$MIME_TYPE" == "text/html" ]]; then
  CSV_FILE="${FILENAME}.csv"
  
  # Extract date (format: "as at 09 Dec 2025") and convert to yyyy-mm-dd
  AS_AT_DATE=$(grep -oiE 'as at [0-9]+ [A-Za-z]+ [0-9]+' "$TEMP_FILE" | head -1 | \
    sed 's/[aA]s at //' | \
    awk '{
      split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec", m, " ")
      for (i=1; i<=12; i++) mon[m[i]] = sprintf("%02d", i)
      printf "%s-%s-%02d", $3, mon[$2], $1
    }')
  
  cat "$TEMP_FILE" |
    tr '\n\r' ' ' |
    sed 's|<[tT][aA][bB][lL][eE]|\n<table|g' |
    grep -i '<table' | head -1 |
    sed 's|</[tT][rR]>|\n|g' |
    awk -v as_at="$AS_AT_DATE" '
    BEGIN { first_row = 1; prev_state = "" }
    {
      col = 0
      delete cells
      line = $0
      
      while (match(line, /<[tT][hHdD][^>]*>[^<]*((<[^\/][^>]*>[^<]*)*(<\/[^tT][^>]*>[^<]*)*)*<\/[tT][hHdD]>/)) {
        cell = substr(line, RSTART, RLENGTH)
        line = substr(line, RSTART + RLENGTH)
        
        content = cell
        gsub(/<[^>]*>/, "", content)
        gsub(/&nbsp;/, " ", content)
        gsub(/&amp;/, "\\&", content)
        gsub(/&rdquo;/, "\"", content)
        gsub(/&rsquo;/, "'", content)
        gsub(/&ndash;/, "-", content)
        gsub(/--/, "N/A", content)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", content)
        gsub(/[[:space:]]+/, " ", content)
        
        col++
        cells[col] = content
      }
      
      if (col > 0) {
        # Fill empty state from previous row
        if (!first_row && cells[1] == "") {
          cells[1] = prev_state
        }
        if (cells[1] != "") {
          prev_state = cells[1]
        }
        
        out = ""
        for (i = 1; i <= col; i++) {
          out = out (i > 1 ? "," : "") cells[i]
        }
        
        if (out !~ /^[[:space:],]*$/) {
          if (first_row) {
            out = out ",Date"
            first_row = 0
          } else {
            out = out "," as_at
          }
          print out
        }
      }
    }
    ' > "$CSV_FILE"
  
  rm -f "$TEMP_FILE"
  echo "Saved: $CSV_FILE"
else
  mv "$TEMP_FILE" "${FILENAME}"
  echo "Saved: ${FILENAME}"
fi
