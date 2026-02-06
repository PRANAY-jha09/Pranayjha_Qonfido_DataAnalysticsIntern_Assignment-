#!/usr/bin/env python3
"""
Data Validation and Quality Checks
For Qonfido MF Automation Output
"""

import pandas as pd
import re


class PortfolioDataValidator:
    """Validates consolidated portfolio data quality"""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.issues = []
    
    def run_all_checks(self):
        """Run comprehensive data quality checks"""
        print("="*60)
        print("DATA QUALITY VALIDATION REPORT")
        print("="*60)
        print(f"File: {self.csv_path}")
        print(f"Total Records: {len(self.df)}")
        print("="*60 + "\n")
        
        self.check_required_fields()
        self.check_isin_format()
        self.check_numeric_ranges()
        self.check_portfolio_percentages()
        self.check_duplicates()
        self.check_missing_values()
        
        self.print_summary()
    
    def check_required_fields(self):
        """Verify all required columns exist"""
        required_fields = [
            'amc_name', 'scheme_name', 'instrument_name', 
            'instrument_type', 'reporting_date'
        ]
        
        missing = [f for f in required_fields if f not in self.df.columns]
        
        if missing:
            self.issues.append(f"Missing required columns: {missing}")
            print("❌ Required Fields Check: FAILED")
            print(f"   Missing: {missing}\n")
        else:
            print("✅ Required Fields Check: PASSED\n")
    
    def check_isin_format(self):
        """Validate ISIN format (should be 12 characters)"""
        if 'isin' not in self.df.columns:
            return
        
        valid_isin_pattern = r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$'
        
        invalid_isins = self.df[
            self.df['isin'].notna() & 
            ~self.df['isin'].str.match(valid_isin_pattern, na=False)
        ]
        
        if len(invalid_isins) > 0:
            self.issues.append(f"Found {len(invalid_isins)} invalid ISIN codes")
            print(f"⚠️  ISIN Format Check: {len(invalid_isins)} issues found")
            print(f"   Sample invalid ISINs: {invalid_isins['isin'].head().tolist()}\n")
        else:
            print("✅ ISIN Format Check: PASSED\n")
    
    def check_numeric_ranges(self):
        """Check if numeric fields are in reasonable ranges"""
        issues_found = False
        
        # Check percentage_of_portfolio (should be 0-100)
        if 'percentage_of_portfolio' in self.df.columns:
            out_of_range = self.df[
                (self.df['percentage_of_portfolio'] < 0) | 
                (self.df['percentage_of_portfolio'] > 100)
            ]
            
            if len(out_of_range) > 0:
                self.issues.append(f"Found {len(out_of_range)} holdings with invalid percentage")
                print(f"⚠️  Percentage Range Check: {len(out_of_range)} issues")
                issues_found = True
        
        # Check market_value (should be positive)
        if 'market_value_lakhs' in self.df.columns:
            negative_values = self.df[self.df['market_value_lakhs'] < 0]
            
            if len(negative_values) > 0:
                self.issues.append(f"Found {len(negative_values)} holdings with negative value")
                print(f"⚠️  Market Value Check: {len(negative_values)} negative values")
                issues_found = True
        
        if not issues_found:
            print("✅ Numeric Range Check: PASSED\n")
        else:
            print()
    
    def check_portfolio_percentages(self):
        """Verify that portfolio percentages sum to ~100% per scheme"""
        if 'percentage_of_portfolio' not in self.df.columns:
            return
        
        scheme_sums = self.df.groupby('scheme_name')['percentage_of_portfolio'].sum()
        
        # Allow 5% deviation (95-105%)
        outlier_schemes = scheme_sums[(scheme_sums < 95) | (scheme_sums > 105)]
        
        if len(outlier_schemes) > 0:
            self.issues.append(f"Found {len(outlier_schemes)} schemes with unusual portfolio sum")
            print(f"⚠️  Portfolio Sum Check: {len(outlier_schemes)} schemes have unusual totals")
            for scheme, total in outlier_schemes.items():
                print(f"   {scheme}: {total:.2f}%")
            print()
        else:
            print("✅ Portfolio Sum Check: PASSED")
            print(f"   Average portfolio sum: {scheme_sums.mean():.2f}%\n")
    
    def check_duplicates(self):
        """Check for duplicate holdings within same scheme"""
        duplicates = self.df[
            self.df.duplicated(subset=['scheme_name', 'instrument_name'], keep=False)
        ]
        
        if len(duplicates) > 0:
            self.issues.append(f"Found {len(duplicates)} duplicate holdings")
            print(f"⚠️  Duplicate Check: {len(duplicates)} potential duplicates")
            print(f"   Sample: {duplicates[['scheme_name', 'instrument_name']].head()}\n")
        else:
            print("✅ Duplicate Check: PASSED\n")
    
    def check_missing_values(self):
        """Report missing value statistics"""
        print("📊 Missing Value Report:")
        print("-" * 60)
        
        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            missing_pct = (missing_count / len(self.df)) * 100
            
            if missing_count > 0:
                print(f"   {col:30s}: {missing_count:5d} ({missing_pct:5.1f}%)")
        
        print()
    
    def print_summary(self):
        """Print overall validation summary"""
        print("="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if len(self.issues) == 0:
            print("✅ All validation checks passed!")
            print("   Data quality: EXCELLENT")
        else:
            print(f"⚠️  Found {len(self.issues)} issue(s):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
            print("\n   Data quality: NEEDS REVIEW")
        
        print("="*60)


def generate_data_profile(csv_path):
    """Generate basic data profiling statistics"""
    df = pd.read_csv(csv_path)
    
    print("\n" + "="*60)
    print("DATA PROFILE")
    print("="*60)
    
    print(f"\n📈 Dataset Overview:")
    print(f"   Total Holdings: {len(df)}")
    print(f"   Unique Schemes: {df['scheme_name'].nunique()}")
    print(f"   Date Range: {df['reporting_date'].unique()}")
    
    print(f"\n💼 Instrument Type Distribution:")
    print(df['instrument_type'].value_counts().to_string())
    
    if 'market_value_lakhs' in df.columns:
        print(f"\n💰 Market Value Statistics (₹ Lakhs):")
        print(f"   Total Value: {df['market_value_lakhs'].sum():,.2f}")
        print(f"   Average Holding: {df['market_value_lakhs'].mean():,.2f}")
        print(f"   Median Holding: {df['market_value_lakhs'].median():,.2f}")
        print(f"   Largest Holding: {df['market_value_lakhs'].max():,.2f}")
    
    print(f"\n🏢 Top 5 Holdings by Value:")
    top_holdings = df.nlargest(5, 'market_value_lakhs')[
        ['instrument_name', 'scheme_name', 'market_value_lakhs', 'percentage_of_portfolio']
    ]
    print(top_holdings.to_string(index=False))
    
    print("="*60)


if __name__ == "__main__":
    import sys
    
    csv_file = "/home/claude/output/consolidated_portfolio.csv"
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    # Run validation
    validator = PortfolioDataValidator(csv_file)
    validator.run_all_checks()
    
    # Generate profile
    generate_data_profile(csv_file)
