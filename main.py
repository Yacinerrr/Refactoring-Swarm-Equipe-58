import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment
from src.utils.analysis_tools.pylint_runner import run_pylint


load_dotenv()

def main():
    
    results = run_pylint("./sandbox")
    for r in results:
        print(r)

    print("✅ MISSION_COMPLETE")

if __name__ == "__main__":
    main()