#!/usr/bin/env python3
"""
Simple test script to test basic CSV functionality with the batch of CSV files
from the Test CSV folder.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import basic parsing functions
from flowproc.domain.parsing import load_and_parse_df, extract_group_animal, extract_tissue


class SimpleCSVTester:
    """Simple test runner for batch CSV processing."""
    
    def __init__(self, csv_folder: Path):
        self.csv_folder = csv_folder
        self.csv_files = list(csv_folder.glob("*.csv"))
        self.test_results = []
        
    def run_basic_csv_tests(self) -> Dict[str, Any]:
        """Test basic CSV loading with all CSV files."""
        print(f"\n🔍 Testing basic CSV loading with {len(self.csv_files)} CSV files...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_loads": 0,
            "failed_loads": 0,
            "errors": [],
            "file_info": []
        }
        
        for csv_file in self.csv_files:
            try:
                print(f"  Testing: {csv_file.name}")
                
                # Test basic CSV loading with pandas
                df = pd.read_csv(csv_file)
                assert not df.empty, f"CSV file {csv_file.name} is empty"
                
                # Collect file information
                file_info = {
                    "name": csv_file.name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_kb": csv_file.stat().st_size / 1024,
                    "column_names": list(df.columns),
                    "data_types": df.dtypes.to_dict()
                }
                results["file_info"].append(file_info)
                
                results["successful_loads"] += 1
                print(f"    ✅ Successfully loaded {csv_file.name} ({len(df)} rows, {len(df.columns)} columns)")
                
            except Exception as e:
                results["failed_loads"] += 1
                error_msg = f"Failed to load {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_parsing_tests(self) -> Dict[str, Any]:
        """Test FlowProcessor parsing with CSV files."""
        print(f"\n⚙️  Testing FlowProcessor parsing...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_parses": 0,
            "failed_parses": 0,
            "errors": []
        }
        
        for csv_file in self.csv_files:
            try:
                print(f"  Testing parsing: {csv_file.name}")
                
                # Test FlowProcessor parsing
                df, sid_col = load_and_parse_df(csv_file)
                assert df is not None, f"Failed to parse {csv_file.name}"
                assert sid_col is not None, f"No sample ID column found in {csv_file.name}"
                
                results["successful_parses"] += 1
                print(f"    ✅ Successfully parsed {csv_file.name} (sample ID col: {sid_col})")
                
            except Exception as e:
                results["failed_parses"] += 1
                error_msg = f"Failed to parse {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_sample_id_tests(self) -> Dict[str, Any]:
        """Test sample ID extraction with CSV files."""
        print(f"\n🆔 Testing sample ID extraction...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_extractions": 0,
            "failed_extractions": 0,
            "errors": []
        }
        
        for csv_file in self.csv_files:
            try:
                print(f"  Testing sample ID extraction: {csv_file.name}")
                
                # Load the CSV
                df = pd.read_csv(csv_file)
                
                # Find potential sample ID columns
                potential_id_cols = []
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['sample', 'id', 'name', 'file']):
                        potential_id_cols.append(col)
                
                if not potential_id_cols:
                    # Try first column if no obvious ID column
                    potential_id_cols = [df.columns[0]]
                
                # Test sample ID extraction
                sample_ids_found = 0
                for col in potential_id_cols:
                    if col in df.columns:
                        sample_values = df[col].dropna().astype(str)
                        if len(sample_values) > 0:
                            # Test extraction on first few values
                            for sample_id in sample_values.head(5):
                                try:
                                    parsed_id = extract_group_animal(sample_id)
                                    if parsed_id is not None:
                                        sample_ids_found += 1
                                        break
                                except:
                                    continue
                
                if sample_ids_found > 0:
                    results["successful_extractions"] += 1
                    print(f"    ✅ Successfully extracted sample IDs from {csv_file.name}")
                else:
                    print(f"    ⚠️  No valid sample IDs found in {csv_file.name}")
                    
            except Exception as e:
                results["failed_extractions"] += 1
                error_msg = f"Failed to extract sample IDs from {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_tissue_extraction_tests(self) -> Dict[str, Any]:
        """Test tissue extraction with CSV files."""
        print(f"\n🧬 Testing tissue extraction...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_extractions": 0,
            "failed_extractions": 0,
            "errors": []
        }
        
        for csv_file in self.csv_files:
            try:
                print(f"  Testing tissue extraction: {csv_file.name}")
                
                # Load the CSV
                df = pd.read_csv(csv_file)
                
                # Find potential sample ID columns
                potential_id_cols = []
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['sample', 'id', 'name', 'file']):
                        potential_id_cols.append(col)
                
                if not potential_id_cols:
                    # Try first column if no obvious ID column
                    potential_id_cols = [df.columns[0]]
                
                # Test tissue extraction
                tissues_found = 0
                for col in potential_id_cols:
                    if col in df.columns:
                        sample_values = df[col].dropna().astype(str)
                        if len(sample_values) > 0:
                            # Test extraction on first few values
                            for sample_id in sample_values.head(5):
                                try:
                                    tissue = extract_tissue(sample_id)
                                    if tissue and tissue != "unknown":
                                        tissues_found += 1
                                        break
                                except:
                                    continue
                
                if tissues_found > 0:
                    results["successful_extractions"] += 1
                    print(f"    ✅ Successfully extracted tissues from {csv_file.name}")
                else:
                    print(f"    ⚠️  No valid tissues found in {csv_file.name}")
                    
            except Exception as e:
                results["failed_extractions"] += 1
                error_msg = f"Failed to extract tissues from {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print(f"🚀 Starting simple CSV tests with {len(self.csv_files)} files...")
        print(f"CSV files found: {[f.name for f in self.csv_files]}")
        
        all_results = {
            "csv_loading": self.run_basic_csv_tests(),
            "parsing": self.run_parsing_tests(),
            "sample_id_extraction": self.run_sample_id_tests(),
            "tissue_extraction": self.run_tissue_extraction_tests()
        }
        
        # Calculate summary statistics
        total_tests = sum(
            all_results[category]["total_files"] 
            for category in all_results
        )
        total_successes = sum(
            all_results[category].get("successful_loads", 0) +
            all_results[category].get("successful_parses", 0) +
            all_results[category].get("successful_extractions", 0)
            for category in all_results
        )
        total_failures = sum(
            all_results[category].get("failed_loads", 0) +
            all_results[category].get("failed_parses", 0) +
            all_results[category].get("failed_extractions", 0)
            for category in all_results
        )
        
        all_results["summary"] = {
            "total_tests": total_tests,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "success_rate": (total_successes / (total_successes + total_failures)) * 100 if (total_successes + total_failures) > 0 else 0
        }
        
        return all_results
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print formatted test results."""
        print("\n" + "="*60)
        print("📋 SIMPLE CSV TEST RESULTS")
        print("="*60)
        
        for category, category_results in results.items():
            if category == "summary":
                continue
                
            print(f"\n{category.upper()} TESTS:")
            print(f"  Total files tested: {category_results['total_files']}")
            
            if "successful_loads" in category_results:
                print(f"  Successful loads: {category_results['successful_loads']}")
                print(f"  Failed loads: {category_results['failed_loads']}")
            elif "successful_parses" in category_results:
                print(f"  Successful parses: {category_results['successful_parses']}")
                print(f"  Failed parses: {category_results['failed_parses']}")
            elif "successful_extractions" in category_results:
                print(f"  Successful extractions: {category_results['successful_extractions']}")
                print(f"  Failed extractions: {category_results['failed_extractions']}")
            
            if category_results.get("errors"):
                print(f"  Errors:")
                for error in category_results["errors"][:3]:  # Show first 3 errors
                    print(f"    - {error}")
                if len(category_results["errors"]) > 3:
                    print(f"    ... and {len(category_results['errors']) - 3} more errors")
        
        # Print file information if available
        if "csv_loading" in results and results["csv_loading"].get("file_info"):
            print(f"\n📁 FILE INFORMATION:")
            for file_info in results["csv_loading"]["file_info"]:
                print(f"  {file_info['name']}: {file_info['rows']} rows, {file_info['columns']} columns, {file_info['size_kb']:.1f} KB")
        
        # Print summary
        summary = results["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"  Total tests: {summary['total_tests']}")
        print(f"  Total successes: {summary['total_successes']}")
        print(f"  Total failures: {summary['total_failures']}")
        print(f"  Success rate: {summary['success_rate']:.1f}%")
        
        if summary['success_rate'] >= 80:
            print("  🎉 Overall result: EXCELLENT")
        elif summary['success_rate'] >= 60:
            print("  ✅ Overall result: GOOD")
        elif summary['success_rate'] >= 40:
            print("  ⚠️  Overall result: FAIR")
        else:
            print("  ❌ Overall result: NEEDS IMPROVEMENT")


def main():
    """Main function to run the simple CSV tests."""
    # Path to the Test CSV folder
    csv_folder = Path("../Test CSV")
    
    if not csv_folder.exists():
        print(f"❌ Error: CSV folder not found at {csv_folder}")
        print("Please ensure the 'Test CSV' folder is in the correct location.")
        return 1
    
    # Create tester and run tests
    tester = SimpleCSVTester(csv_folder)
    
    try:
        results = tester.run_all_tests()
        tester.print_results(results)
        
        # Return appropriate exit code
        if results["summary"]["success_rate"] >= 60:
            print("\n✅ Simple CSV tests completed successfully!")
            return 0
        else:
            print("\n❌ Simple CSV tests completed with significant failures.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main()) 