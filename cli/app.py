from __future__ import annotations

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from cli.menu import display_menu
from cli import commands

def main():
    parser = argparse.ArgumentParser(description="AI Receptionist Evaluation Framework CLI")
    parser.add_argument("--run-all", action="store_true", help="Run benchmark, generate dashboard, and export reports")
    
    # Parse known args so that if other arguments are passed they don't break the script,
    # or just parse args and let it error if unknown args are passed.
    args, unknown = parser.parse_known_args()
    
    if args.run_all:
        print("Running all automated benchmark tasks...")
        commands.benchmark_direct()
        commands.generate_dashboard()
        commands.export_reports()
        print("\nAll tasks completed!")
    else:
        display_menu()

if __name__ == "__main__":
    main()
