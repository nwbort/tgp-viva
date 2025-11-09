#!/usr/bin/env python3
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz
import sys

def clean_col_names(df):
    """Cleans DataFrame column names to be more like R's janitor::clean_names."""
    cols = df.columns
    new_cols = []
    for col in cols:
        # Replace <br> tags and multiple spaces with a single underscore
        new_col = re.sub(r'<br/?>|\s+', '_', col)
        # Convert to lowercase
        new_col = new_col.lower()
        # Remove any character that is not a letter, number, or underscore
        new_col = re.sub(r'[^\w]+', '', new_col)
        # Remove leading/trailing underscores
        new_col = new_col.strip('_')
        new_cols.append(new_col)
    df.columns = new_cols
    return df

def main():
    """
    Scrapes terminal gate pricing from Viva Energy, processes it, and saves to CSV.
    """
    URL = "https://www.vivaenergy.com.au/quick-links/terminal-gate-pricing"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
    HEADERS = {'User-Agent': USER_AGENT}
    OUTPUT_FILENAME = "viva_tgp_latest.csv"

    try:
        # --- Fetch and parse the page ---
        print(f"Fetching data from {URL}")
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'lxml')

        # --- Extract the effective date ---
        print("Extracting effective date...")
        h4_tag = soup.find('h4', string=re.compile("as at", re.IGNORECASE))
        if not h4_tag:
            raise ValueError("Could not find the h4 tag with the effective date.")
        
        date_match = re.search(r'(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})', h4_tag.text)
        if not date_match:
            raise ValueError("Could not parse the date from the h4 tag.")
            
        date_str = date_match.group(1)
        effective_date = datetime.strptime(date_str, "%d %b %Y").date()
        print(f"Found effective date: {effective_date.isoformat()}")

        # --- Extract and process the table using pandas ---
        print("Extracting and processing the table...")
        tables = pd.read_html(response.text, attrs={'class': 'tgp-table'})
        
        if not tables:
            raise ValueError("Could not find the TGP table on the page.")
            
        df = tables[0]

        # --- Clean the DataFrame (replicating R script logic) ---
        
        # 1. Clean column names
        df = clean_col_names(df)
        
        # 2. Fill down the 'state' column
        df['state'] = df['state'].ffill()
        
        # 3. Drop any rows where 'city' is missing
        df.dropna(subset=['city'], inplace=True)
        
        # 4. Convert price columns to numeric, coercing errors ('--') to NaN
        price_cols = [col for col in df.columns if col not in ['state', 'city']]
        for col in price_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # 5. Add effective_date and date_downloaded columns
        df['effective_date'] = effective_date.isoformat()
        df['date_downloaded'] = datetime.now(pytz.utc).isoformat()

        # --- Save the data ---
        print(f"Saving data to {OUTPUT_FILENAME}")
        df.to_csv(OUTPUT_FILENAME, index=False)
        print("Scraping completed successfully.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, IndexError) as e:
        print(f"Error parsing the page content: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
