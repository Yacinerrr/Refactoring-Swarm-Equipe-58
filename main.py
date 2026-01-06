import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment
from src.utils.analysis_tools.pytest_runner import run_pytest
from src.utils.analysis_tools.analyze import analyze_sandbox



load_dotenv()

def main():
    
    results = analyze_sandbox("./sandbox")
    for r in results:
        print(r)

    print("✅ MISSION_COMPLETE")

if __name__ == "__main__":
    main()