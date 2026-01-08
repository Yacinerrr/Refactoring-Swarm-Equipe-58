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
                               #TODO  LAZM YMACHI MEME MAYMDLKCHE STRECTUR ANTIC
    print("✅ MISSION_COMPLETE")
         #!    BALKKK TSEPARE LES TEST ET LE CODE 
if __name__ == "__main__":
    main()     #! LES DEUX QUSTION  1.ASM LES FICHER IDA HWA 3TANA LES TEST 2. ASK HWA YRTINA LES TEST 