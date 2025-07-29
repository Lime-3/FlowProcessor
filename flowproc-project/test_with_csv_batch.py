#!/usr/bin/env python3
"""
Custom test script to run FlowProcessor tests with the batch of CSV files
from the Test CSV folder.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest
from typing import List, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import FlowProcessor modules
from flowproc.domain.parsing.service import ParseService
from flowproc.domain.processing.service import DataProcessingService
from flowproc.domain.export.service import ExportService
from flowproc.domain.visualization.service import VisualizationService
from flowproc.core.models import ProcessingConfig


class CSVBatchTester:
    """Test runner for batch CSV processing."""
    
    def __init__(self, csv_folder: Path):
        self.csv_folder = csv_folder
        self.csv_files = list(csv_folder.glob("*.csv"))
        self.test_results = []
        
    def run_basic_parsing_tests(self) -> Dict[str, Any]:
        """Test basic parsing functionality with all CSV files."""
        print(f"\n🔍 Testing basic parsing with {len(self.csv_files)} CSV files...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_parses": 0,
            "failed_parses": 0,
            "errors": []
        }
        
        parser = ParseService()
        
        for csv_file in self.csv_files:
            try:
                print(f"  Testing: {csv_file.name}")
                
                # Test basic CSV loading
                df = pd.read_csv(csv_file)
                assert not df.empty, f"CSV file {csv_file.name} is empty"
                
                # Test parsing with FlowProcessor
                parsed_data = parser.parse_file(csv_file, "default")
                assert parsed_data is not None, f"Failed to parse {csv_file.name}"
                
                results["successful_parses"] += 1
                print(f"    ✅ Successfully parsed {csv_file.name} ({len(df)} rows)")
                
            except Exception as e:
                results["failed_parses"] += 1
                error_msg = f"Failed to parse {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_processing_tests(self) -> Dict[str, Any]:
        """Test data processing with a subset of CSV files."""
        print(f"\n⚙️  Testing data processing...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_processing": 0,
            "failed_processing": 0,
            "errors": []
        }
        
        processor = DataProcessingService()
        
        # Test with first 3 CSV files to avoid overwhelming the system
        test_files = self.csv_files[:3]
        
        for csv_file in test_files:
            try:
                print(f"  Processing: {csv_file.name}")
                
                # Create a temporary output directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Create processing config
                    config = ProcessingConfig(
                        input_paths=[csv_file],
                        output_dir=temp_path / "output",
                        time_course_mode=False,
                        auto_parse_groups=True,
                        max_workers=1
                    )
                    
                    # Test processing
                    # First load the data
                    df = pd.read_csv(csv_file)
                    processed_data = processor.process_data(df, {
                        'aggregate': False,
                        'transform': False
                    })
                    assert processed_data is not None, f"Failed to process {csv_file.name}"
                    
                    results["successful_processing"] += 1
                    print(f"    ✅ Successfully processed {csv_file.name}")
                    
            except Exception as e:
                results["failed_processing"] += 1
                error_msg = f"Failed to process {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_visualization_tests(self) -> Dict[str, Any]:
        """Test visualization with sample CSV files."""
        print(f"\n📊 Testing visualization...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_visualizations": 0,
            "failed_visualizations": 0,
            "errors": []
        }
        
        viz_service = VisualizationService()
        
        # Test with first 2 CSV files
        test_files = self.csv_files[:2]
        
        for csv_file in test_files:
            try:
                print(f"  Visualizing: {csv_file.name}")
                
                # Load and parse the CSV
                df = pd.read_csv(csv_file)
                
                # Find numeric columns for visualization
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if len(numeric_cols) > 0:
                    # Test with first numeric column
                    metric_col = numeric_cols[0]
                    
                    # Create a simple visualization config
                    viz_config = {
                        "metric": metric_col,
                        "time_course_mode": False,
                        "auto_parse_groups": True
                    }
                    
                    # Test visualization
                    fig = viz_service.create_plot(df, 'bar', {
                        'x': df.columns[0] if len(df.columns) > 0 else None,
                        'y': metric_col,
                        'title': f'Test plot for {csv_file.name}'
                    })
                    assert fig is not None, f"Failed to create visualization for {csv_file.name}"
                    
                    results["successful_visualizations"] += 1
                    print(f"    ✅ Successfully visualized {csv_file.name} (metric: {metric_col})")
                else:
                    print(f"    ⚠️  No numeric columns found in {csv_file.name}")
                    
            except Exception as e:
                results["failed_visualizations"] += 1
                error_msg = f"Failed to visualize {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_export_tests(self) -> Dict[str, Any]:
        """Test export functionality with sample CSV files."""
        print(f"\n📤 Testing export functionality...")
        
        results = {
            "total_files": len(self.csv_files),
            "successful_exports": 0,
            "failed_exports": 0,
            "errors": []
        }
        
        exporter = ExportService()
        
        # Test with first 2 CSV files
        test_files = self.csv_files[:2]
        
        for csv_file in test_files:
            try:
                print(f"  Exporting: {csv_file.name}")
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Load the CSV
                    df = pd.read_csv(csv_file)
                    
                    # Test Excel export
                    output_file = temp_path / f"{csv_file.stem}_export.xlsx"
                    
                    # Create export config
                    export_config = {
                        "output_path": output_file,
                        "sheet_name": "Data",
                        "include_summary": True
                    }
                    
                    # Test export
                    exporter.export_data(df, str(output_file), 'excel', export_config)
                    
                    # Verify file was created
                    assert output_file.exists(), f"Export file not created for {csv_file.name}"
                    
                    results["successful_exports"] += 1
                    print(f"    ✅ Successfully exported {csv_file.name} to Excel")
                    
            except Exception as e:
                results["failed_exports"] += 1
                error_msg = f"Failed to export {csv_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ❌ {error_msg}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print(f"🚀 Starting batch CSV tests with {len(self.csv_files)} files...")
        print(f"CSV files found: {[f.name for f in self.csv_files]}")
        
        all_results = {
            "parsing": self.run_basic_parsing_tests(),
            "processing": self.run_processing_tests(),
            "visualization": self.run_visualization_tests(),
            "export": self.run_export_tests()
        }
        
        # Calculate summary statistics
        total_tests = sum(
            all_results[category]["total_files"] 
            for category in all_results
        )
        total_successes = sum(
            all_results[category].get("successful_parses", 0) +
            all_results[category].get("successful_processing", 0) +
            all_results[category].get("successful_visualizations", 0) +
            all_results[category].get("successful_exports", 0)
            for category in all_results
        )
        total_failures = sum(
            all_results[category].get("failed_parses", 0) +
            all_results[category].get("failed_processing", 0) +
            all_results[category].get("failed_visualizations", 0) +
            all_results[category].get("failed_exports", 0)
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
        print("📋 BATCH CSV TEST RESULTS")
        print("="*60)
        
        for category, category_results in results.items():
            if category == "summary":
                continue
                
            print(f"\n{category.upper()} TESTS:")
            print(f"  Total files tested: {category_results['total_files']}")
            
            if "successful_parses" in category_results:
                print(f"  Successful parses: {category_results['successful_parses']}")
                print(f"  Failed parses: {category_results['failed_parses']}")
            elif "successful_processing" in category_results:
                print(f"  Successful processing: {category_results['successful_processing']}")
                print(f"  Failed processing: {category_results['failed_processing']}")
            elif "successful_visualizations" in category_results:
                print(f"  Successful visualizations: {category_results['successful_visualizations']}")
                print(f"  Failed visualizations: {category_results['failed_visualizations']}")
            elif "successful_exports" in category_results:
                print(f"  Successful exports: {category_results['successful_exports']}")
                print(f"  Failed exports: {category_results['failed_exports']}")
            
            if category_results.get("errors"):
                print(f"  Errors:")
                for error in category_results["errors"][:3]:  # Show first 3 errors
                    print(f"    - {error}")
                if len(category_results["errors"]) > 3:
                    print(f"    ... and {len(category_results['errors']) - 3} more errors")
        
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
    """Main function to run the batch CSV tests."""
    # Path to the Test CSV folder
    csv_folder = Path("../Test CSV")
    
    if not csv_folder.exists():
        print(f"❌ Error: CSV folder not found at {csv_folder}")
        print("Please ensure the 'Test CSV' folder is in the correct location.")
        return 1
    
    # Create tester and run tests
    tester = CSVBatchTester(csv_folder)
    
    try:
        results = tester.run_all_tests()
        tester.print_results(results)
        
        # Return appropriate exit code
        if results["summary"]["success_rate"] >= 60:
            print("\n✅ Batch tests completed successfully!")
            return 0
        else:
            print("\n❌ Batch tests completed with significant failures.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main()) 