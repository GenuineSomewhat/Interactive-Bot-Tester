"""
Testing utilities for spreadsheet functionality in the interactive bot tester.
Use this to test spreadsheet generation and serving locally.
"""

import sys
from pathlib import Path
import json
from typing import Dict, Any, Optional
import webbrowser
import platform
import subprocess

# Add bot directory to path for imports
bot_path = Path(__file__).parent.parent / "bot"
if str(bot_path) not in sys.path:
    sys.path.insert(0, str(bot_path))

from spreadsheet_service import (
    generate_excel_from_data,
    get_spreadsheet_path,
    get_all_active_spreadsheets,
)
from spreadsheet_commands import SpreadsheetCommands


class SpreadsheetTester:
    """Utilities for testing spreadsheet generation locally."""
    
    def __init__(self, use_browser: bool = True):
        """
        Initialize the tester.
        
        Args:
            use_browser: Automatically open generated files in default app
        """
        self.use_browser = use_browser
        self.generated_sheets = []
    
    def test_basic_spreadsheet(self) -> str:
        """
        Test basic spreadsheet generation.
        
        Returns:
            sheet_id of the generated spreadsheet
        """
        print("\n[TEST] Generating basic spreadsheet...")
        
        data = {
            "Sample Data": [
                {"Name": "Alice", "Score": 100, "Status": "Active"},
                {"Name": "Bob", "Score": 85, "Status": "Active"},
                {"Name": "Charlie", "Score": 92, "Status": "Inactive"},
                {"Name": "Diana", "Score": 88, "Status": "Active"},
            ]
        }
        
        sheet_id = generate_excel_from_data(data, "Sample Spreadsheet")
        self.generated_sheets.append(sheet_id)
        
        file_path = get_spreadsheet_path(sheet_id)
        print(f"✓ Generated: {file_path}")
        print(f"  Sheet ID: {sheet_id}")
        
        return sheet_id
    
    def test_leaderboard_spreadsheet(self) -> str:
        """
        Test leaderboard spreadsheet generation.
        
        Returns:
            sheet_id of the generated leaderboard
        """
        print("\n[TEST] Generating leaderboard spreadsheet...")
        
        leaderboard = {
            "Alice": 1500,
            "Bob": 1200,
            "Charlie": 1100,
            "Diana": 950,
        }
        
        result = SpreadsheetCommands.get_leaderboard_spreadsheet(leaderboard)
        sheet_id = result["sheet_id"]
        self.generated_sheets.append(sheet_id)
        
        file_path = get_spreadsheet_path(sheet_id)
        print(f"✓ Generated: {file_path}")
        print(f"  Sheet ID: {sheet_id}")
        print(f"  Rows: {result['rows_count']}")
        
        return sheet_id
    
    def test_game_stats_spreadsheet(self) -> str:
        """
        Test game statistics spreadsheet.
        
        Returns:
            sheet_id of the generated game stats
        """
        print("\n[TEST] Generating game statistics spreadsheet...")
        
        game_stats = {
            "Plane Game": {
                "Total Rounds": 42,
                "Correct Answers": 31,
                "Accuracy": "73.8%"
            },
            "Gun Game": {
                "Total Rounds": 38,
                "Correct Answers": 28,
                "Accuracy": "73.7%"
            }
        }
        
        result = SpreadsheetCommands.get_game_stats_spreadsheet(
            game_stats,
            game_name="Bot Games"
        )
        sheet_id = result["sheet_id"]
        self.generated_sheets.append(sheet_id)
        
        file_path = get_spreadsheet_path(sheet_id)
        print(f"✓ Generated: {file_path}")
        print(f"  Sheet ID: {sheet_id}")
        print(f"  Rows: {result['rows_count']}")
        
        return sheet_id
    
    def test_custom_data(self, data: Dict[str, Any], title: str = "Test") -> str:
        """
        Test with custom data.
        
        Args:
            data: Custom data dictionary
            title: Title for the spreadsheet
        
        Returns:
            sheet_id of the generated spreadsheet
        """
        print(f"\n[TEST] Generating custom spreadsheet: {title}...")
        
        sheet_id = generate_excel_from_data(data, title)
        self.generated_sheets.append(sheet_id)
        
        file_path = get_spreadsheet_path(sheet_id)
        print(f"✓ Generated: {file_path}")
        print(f"  Sheet ID: {sheet_id}")
        
        return sheet_id
    
    def open_spreadsheet(self, sheet_id: str) -> bool:
        """
        Open a spreadsheet in the default application.
        
        Args:
            sheet_id: The spreadsheet ID to open
        
        Returns:
            True if opened successfully
        """
        file_path = get_spreadsheet_path(sheet_id)
        
        if not file_path:
            print(f"✗ Spreadsheet {sheet_id} not found or expired")
            return False
        
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', file_path])
            elif platform.system() == 'Windows':
                import os
                os.startfile(file_path)
            else:  # Linux
                subprocess.Popen(['xdg-open', file_path])
            
            print(f"✓ Opened spreadsheet: {file_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to open spreadsheet: {e}")
            return False
    
    def list_generated_sheets(self) -> None:
        """Display all currently active spreadsheets."""
        print("\n[TEST] Active Spreadsheets:")
        
        active = get_all_active_spreadsheets()
        
        if not active:
            print("  (none)")
            return
        
        for sheet in active:
            print(f"  • {sheet['sheet_id']}")
            print(f"    Created: {sheet['created_at']}")
            print(f"    Expires: {sheet['expires_at']}")
    
    def verify_spreadsheet_file(self, sheet_id: str) -> bool:
        """
        Verify that a spreadsheet file exists and is readable.
        
        Args:
            sheet_id: The spreadsheet ID to verify
        
        Returns:
            True if file exists and is readable
        """
        file_path = get_spreadsheet_path(sheet_id)
        
        if not file_path:
            print(f"✗ Spreadsheet {sheet_id} not found")
            return False
        
        path = Path(file_path)
        if not path.exists():
            print(f"✗ File does not exist: {file_path}")
            return False
        
        if not path.is_file():
            print(f"✗ Path is not a file: {file_path}")
            return False
        
        print(f"✓ Spreadsheet verified: {file_path}")
        print(f"  Size: {path.stat().st_size} bytes")
        
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all tests and return results.
        
        Returns:
            Dictionary with test results
        """
        print("=" * 60)
        print("SPREADSHEET FUNCTIONALITY TESTS")
        print("=" * 60)
        
        results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "sheet_ids": []
        }
        
        try:
            # Test 1: Basic spreadsheet
            print("\n[1/3] Testing basic spreadsheet generation...")
            sheet_id = self.test_basic_spreadsheet()
            if self.verify_spreadsheet_file(sheet_id):
                results["tests_passed"] += 1
            else:
                results["tests_failed"] += 1
            results["sheet_ids"].append(sheet_id)
            results["tests_run"] += 1
            
            # Test 2: Leaderboard
            print("\n[2/3] Testing leaderboard generation...")
            sheet_id = self.test_leaderboard_spreadsheet()
            if self.verify_spreadsheet_file(sheet_id):
                results["tests_passed"] += 1
            else:
                results["tests_failed"] += 1
            results["sheet_ids"].append(sheet_id)
            results["tests_run"] += 1
            
            # Test 3: Game stats
            print("\n[3/3] Testing game statistics generation...")
            sheet_id = self.test_game_stats_spreadsheet()
            if self.verify_spreadsheet_file(sheet_id):
                results["tests_passed"] += 1
            else:
                results["tests_failed"] += 1
            results["sheet_ids"].append(sheet_id)
            results["tests_run"] += 1
            
        except Exception as e:
            print(f"\n✗ Test error: {e}")
            results["tests_failed"] += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {results['tests_run']}")
        print(f"Passed: {results['tests_passed']}")
        print(f"Failed: {results['tests_failed']}")
        print(f"Generated IDs: {results['sheet_ids']}")
        
        self.list_generated_sheets()
        
        print("\n" + "=" * 60)
        
        return results


# Standalone test runner
if __name__ == "__main__":
    tester = SpreadsheetTester(use_browser=False)
    results = tester.run_all_tests()
    
    # Print generated sheet IDs for user reference
    print("\nGenerated Spreadsheet IDs (for manual testing):")
    for sheet_id in results["sheet_ids"]:
        print(f"  {sheet_id}")
