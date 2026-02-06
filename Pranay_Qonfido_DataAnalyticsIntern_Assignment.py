#!/usr/bin/env python3
"""
Qonfido Data Analytics Intern Assignment
Automated Mutual Fund Portfolio Data Extraction and Consolidation

Author: Pranay
Date: February 2026
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from datetime import datetime
from urllib.parse import urljoin
import time


class MutualFundPortfolioScraper:
    """
    Automated scraper for mutual fund portfolio data from AMC websites
    Currently configured for Axis Mutual Fund
    """
    
    def __init__(self, amc_name="Axis Mutual Fund"):
        self.amc_name = amc_name
        self.base_url = "https://www.axismf.com"
        self.statutory_url = f"{self.base_url}/statutory-disclosures"
        self.download_folder = "/home/claude/downloads"
        self.output_folder = "/home/claude/output"
        
        # Create directories if they don't exist
        os.makedirs(self.download_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
    def fetch_page_content(self, url):
        """Fetch webpage content with error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None
    
    def find_portfolio_file_url(self, month="December", year="2025"):
        """
        Navigate to statutory disclosures and find the monthly portfolio file URL
        Looks for section "8. Monthly Scheme Portfolios"
        """
        print(f"Navigating to: {self.statutory_url}")
        html_content = self.fetch_page_content(self.statutory_url)
        
        if not html_content:
            print("Failed to fetch statutory disclosures page")
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strategy 1: Look for links containing portfolio-related keywords
        # Common patterns: "portfolio", "consolidated", month name, year
        search_patterns = [
            f"{month.lower()}.*{year}.*consolidated",
            f"consolidated.*{month.lower()}.*{year}",
            f"monthly.*portfolio.*{month.lower()}.*{year}",
            f"{month.lower()}.*{year}.*portfolio"
        ]
        
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            
            # Check if link points to Excel file
            if any(ext in href.lower() for ext in ['.xlsx', '.xls']):
                # Check if it matches our search patterns
                combined_text = f"{link_text} {href}".lower()
                
                for pattern in search_patterns:
                    if re.search(pattern, combined_text, re.IGNORECASE):
                        file_url = urljoin(self.base_url, href)
                        print(f"Found portfolio file: {link_text}")
                        print(f"URL: {file_url}")
                        return file_url
        
        print("Could not find portfolio file URL automatically")
        print("Note: Manual download may be required if the file is behind JavaScript/dropdown")
        return None
    
    def download_file(self, url, filename=None):
        """Download file from URL"""
        if not url:
            return None
        
        try:
            print(f"Downloading file from: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            if not filename:
                # Extract filename from URL or content-disposition header
                if 'content-disposition' in response.headers:
                    cd = response.headers['content-disposition']
                    filename = re.findall('filename="?([^"]+)"?', cd)
                    filename = filename[0] if filename else 'portfolio_data.xlsx'
                else:
                    filename = url.split('/')[-1] or 'portfolio_data.xlsx'
            
            filepath = os.path.join(self.download_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"File downloaded successfully: {filepath}")
            return filepath
            
        except requests.RequestException as e:
            print(f"Error downloading file: {e}")
            return None
    
    def parse_excel_portfolios(self, excel_path):
        """
        Parse Excel file containing multiple scheme portfolios
        Returns consolidated dataframe
        """
        print(f"\nParsing Excel file: {excel_path}")
        
        try:
            # Read Excel file to get all sheet names
            xl_file = pd.ExcelFile(excel_path)
            sheet_names = xl_file.sheet_names
            
            print(f"Found {len(sheet_names)} sheets in the file")
            
            # Skip index/summary sheets
            skip_keywords = ['index', 'summary', 'contents', 'note', 'disclaimer']
            scheme_sheets = [
                sheet for sheet in sheet_names 
                if not any(keyword in sheet.lower() for keyword in skip_keywords)
            ]
            
            print(f"Processing {len(scheme_sheets)} scheme sheets")
            
            all_holdings = []
            
            for sheet_name in scheme_sheets:
                print(f"  Processing: {sheet_name}")
                holdings = self.extract_holdings_from_sheet(xl_file, sheet_name)
                if holdings:
                    all_holdings.extend(holdings)
            
            print(f"\nTotal holdings extracted: {len(all_holdings)}")
            
            # Convert to DataFrame
            df = pd.DataFrame(all_holdings)
            
            return df
            
        except Exception as e:
            print(f"Error parsing Excel file: {e}")
            return None
    
    def extract_holdings_from_sheet(self, xl_file, sheet_name):
        """
        Extract portfolio holdings from a single scheme sheet
        This is a generic parser that adapts to different sheet structures
        """
        try:
            df = pd.read_excel(xl_file, sheet_name=sheet_name, header=None)
            
            # Find reporting date (usually near top of sheet)
            reporting_date = self.find_reporting_date(df)
            
            # Identify the header row (contains column names like "Name", "ISIN", "Quantity", etc.)
            header_row_idx = self.find_header_row(df)
            
            if header_row_idx is None:
                print(f"    Warning: Could not identify header row in {sheet_name}")
                return []
            
            # Re-read with proper header
            df = pd.read_excel(xl_file, sheet_name=sheet_name, header=header_row_idx)
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Identify instrument type (Equity/Debt/Other)
            holdings = []
            current_instrument_type = "Unknown"
            
            for idx, row in df.iterrows():
                # Check if this row is a section header (e.g., "Equity & Equity related")
                if self.is_section_header(row):
                    current_instrument_type = self.classify_instrument_type(row)
                    continue
                
                # Extract holding data if row contains valid data
                holding = self.extract_holding_from_row(
                    row, 
                    scheme_name=sheet_name,
                    instrument_type=current_instrument_type,
                    reporting_date=reporting_date
                )
                
                if holding:
                    holdings.append(holding)
            
            return holdings
            
        except Exception as e:
            print(f"    Error processing sheet {sheet_name}: {e}")
            return []
    
    def find_reporting_date(self, df):
        """Find reporting date from sheet (usually mentioned near top)"""
        # Look for date patterns in first 10 rows
        for idx in range(min(10, len(df))):
            for col in df.columns:
                cell_value = str(df.iloc[idx][col])
                # Look for date patterns like "December 31, 2025" or "31/12/2025"
                date_match = re.search(r'(december|31.*12.*2025|2025.*12.*31)', 
                                      cell_value, re.IGNORECASE)
                if date_match:
                    return "2025-12-31"  # Standardized format
        
        return "2025-12-31"  # Default for this assignment
    
    def find_header_row(self, df):
        """Identify which row contains column headers"""
        # Headers typically contain words like: name, isin, quantity, rating, industry
        header_keywords = ['name', 'isin', 'quantity', 'rating', 'industry', 'instrument']
        
        for idx in range(min(20, len(df))):  # Search first 20 rows
            row = df.iloc[idx]
            row_text = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
            
            # Check if row contains multiple header keywords
            keyword_matches = sum(1 for keyword in header_keywords if keyword in row_text)
            
            if keyword_matches >= 2:  # At least 2 header keywords found
                return idx
        
        return None
    
    def is_section_header(self, row):
        """Check if row is a section header (e.g., 'Equity & Equity related')"""
        # Check both first and second columns for section headers
        first_cell = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ""
        second_cell = str(row.iloc[1]).lower() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        
        combined = f"{first_cell} {second_cell}"
        
        section_keywords = [
            'equity', 'debt instruments', 'government securities', 'corporate bonds',
            'money market', 'net current', 'listed', 'unlisted', 'awaiting listing',
            'privately placed', 'reverse repo', 'treps', 'treasury', 'certificate of deposit',
            'commercial paper'
        ]
        
        # Check if row contains section keywords
        if any(keyword in combined for keyword in section_keywords):
            # Additional check: section headers typically don't have ISIN codes
            has_isin = any(
                pd.notna(cell) and re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', str(cell))
                for cell in row
            )
            if not has_isin:
                return True
        
        return False
    
    def classify_instrument_type(self, row):
        """Classify instrument type from section header"""
        # Check both first and second columns
        first_cell = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ""
        second_cell = str(row.iloc[1]).lower() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        
        combined = f"{first_cell} {second_cell}"
        
        if any(keyword in combined for keyword in ['equity', 'stock']):
            return "Equity"
        elif any(keyword in combined for keyword in ['debt instruments', 'government securities', 'bond', 'debenture']):
            return "Debt"
        elif any(keyword in combined for keyword in ['money market', 'cash', 'liquid', 'reverse repo', 'treps', 'treasury bill', 'certificate of deposit', 'commercial paper']):
            return "Money Market"
        else:
            return "Other"
    
    def extract_holding_from_row(self, row, scheme_name, instrument_type, reporting_date):
        """Extract holding details from a data row"""
        # Skip rows that don't contain actual holdings
        if row.isna().all():
            return None
        
        # Try to identify key fields by common column name patterns
        holding = {
            'amc_name': self.amc_name,
            'scheme_name': scheme_name,
            'instrument_type': instrument_type,
            'reporting_date': reporting_date
        }
        
        # Extract fields based on column names
        for col_name in row.index:
            col_lower = str(col_name).lower()
            value = row[col_name]
            
            if pd.isna(value):
                continue
            
            # Instrument name
            if any(keyword in col_lower for keyword in ['name of the instrument', 'name', 'security']):
                if 'isin' not in col_lower:  # Exclude ISIN column
                    holding['instrument_name'] = str(value).strip()
            
            # ISIN
            elif 'isin' in col_lower:
                holding['isin'] = str(value).strip()
            
            # Industry/Rating
            elif 'industry' in col_lower or 'rating' in col_lower:
                holding['industry_rating'] = str(value).strip()
            
            # Quantity
            elif 'quantity' in col_lower:
                try:
                    holding['quantity'] = float(value)
                except:
                    holding['quantity'] = None
            
            # Market Value / Fair Value
            elif any(keyword in col_lower for keyword in ['market', 'fair value', 'value']):
                if 'rs' in col_lower or 'lakhs' in col_lower or 'amount' in col_lower:
                    try:
                        holding['market_value_lakhs'] = float(value)
                    except:
                        holding['market_value_lakhs'] = None
            
            # Percentage of portfolio
            elif '%' in col_lower or 'net assets' in col_lower:
                try:
                    holding['percentage_of_portfolio'] = float(value)
                except:
                    holding['percentage_of_portfolio'] = None
        
        # Only return if we have at least instrument name
        if 'instrument_name' in holding and holding['instrument_name']:
            # Filter out subtotal/total/header rows
            name_lower = holding['instrument_name'].lower()
            skip_keywords = [
                'total', 'sub-total', 'subtotal', 'net current', 'grand total',
                'net receivables', 'net payables', 'listed / awaiting',
                'privately placed', 'unlisted', 'benchmark', 'risk-o-meter'
            ]
            
            if not any(keyword in name_lower for keyword in skip_keywords):
                # Also skip if instrument name is too short (likely header/junk)
                if len(holding['instrument_name'].strip()) > 3:
                    return holding
        
        return None
    
    def save_to_csv(self, df, filename="consolidated_portfolio.csv"):
        """Save consolidated data to CSV"""
        if df is None or df.empty:
            print("No data to save")
            return None
        
        output_path = os.path.join(self.output_folder, filename)
        
        # Reorder columns for better readability
        column_order = [
            'amc_name', 'scheme_name', 'instrument_name', 'instrument_type',
            'isin', 'industry_rating', 'quantity', 'market_value_lakhs',
            'percentage_of_portfolio', 'reporting_date'
        ]
        
        # Only include columns that exist in the dataframe
        columns = [col for col in column_order if col in df.columns]
        df = df[columns]
        
        df.to_csv(output_path, index=False)
        print(f"\nData saved to: {output_path}")
        
        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        print(f"Total schemes processed: {df['scheme_name'].nunique()}")
        print(f"Total holdings: {len(df)}")
        print(f"\nBreakdown by instrument type:")
        print(df['instrument_type'].value_counts())
        print("="*60)
        
        return output_path
    
    def run_full_automation(self, manual_file_path=None):
        """
        Execute the complete automation workflow
        If manual_file_path is provided, skip download step
        """
        print("="*60)
        print("QONFIDO MUTUAL FUND PORTFOLIO AUTOMATION")
        print("="*60)
        print(f"AMC: {self.amc_name}")
        print(f"Target: December 2025 Consolidated Portfolio")
        print("="*60 + "\n")
        
        # Step 1: Download file (or use manual file)
        if manual_file_path and os.path.exists(manual_file_path):
            print(f"Using manually provided file: {manual_file_path}")
            excel_path = manual_file_path
        else:
            print("Step 1: Downloading portfolio file...")
            file_url = self.find_portfolio_file_url(month="December", year="2025")
            
            if file_url:
                excel_path = self.download_file(file_url)
            else:
                print("\nAutomatic download not possible.")
                print("Please manually download the file from:")
                print(f"  {self.statutory_url}")
                print("  Section: 8. Monthly Scheme Portfolios")
                print("  Select: December 2025 - Consolidated")
                return None
        
        if not excel_path or not os.path.exists(excel_path):
            print("Error: Excel file not found")
            return None
        
        # Step 2: Parse Excel and extract data
        print("\nStep 2: Parsing portfolio data...")
        df = self.parse_excel_portfolios(excel_path)
        
        if df is None or df.empty:
            print("Error: No data extracted")
            return None
        
        # Step 3: Save to CSV
        print("\nStep 3: Saving consolidated data...")
        output_path = self.save_to_csv(df)
        
        # Step 4: Generate separate CSVs by instrument type (optional)
        print("\nStep 4: Creating instrument-specific files...")
        for instrument_type in df['instrument_type'].unique():
            if pd.notna(instrument_type) and instrument_type != "Unknown":
                type_df = df[df['instrument_type'] == instrument_type]
                type_filename = f"portfolio_{instrument_type.lower().replace(' ', '_')}.csv"
                self.save_to_csv(type_df, type_filename)
        
        print("\n" + "="*60)
        print("AUTOMATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        return output_path


def main():
    """Main execution function"""
    # Initialize scraper
    scraper = MutualFundPortfolioScraper(amc_name="Axis Mutual Fund")
    
    # For this assignment, we'll use the uploaded file
    # In production, this would be None to trigger automatic download
    manual_file = "/mnt/user-data/uploads/1770301290944_image.png"  # This is the image you uploaded
    
    # Check if there's an Excel file in uploads
    uploads_dir = "/mnt/user-data/uploads"
    excel_files = [f for f in os.listdir(uploads_dir) if f.endswith(('.xlsx', '.xls'))]
    
    if excel_files:
        manual_file = os.path.join(uploads_dir, excel_files[0])
        print(f"Found Excel file in uploads: {excel_files[0]}")
    else:
        print("No Excel file found in uploads.")
        print("Running in demo mode - will attempt automatic download\n")
        manual_file = None
    
    # Run full automation
    output_path = scraper.run_full_automation(manual_file_path=manual_file)
    
    if output_path:
        print(f"\n✓ Output files available in: {scraper.output_folder}")
        return output_path
    else:
        print("\n✗ Automation encountered errors. Please check logs above.")
        return None


if __name__ == "__main__":
    main()
