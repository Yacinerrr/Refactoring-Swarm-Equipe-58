import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment
from src.utils.analysis_tools.pytest_runner import run_pytest
from src.utils.analysis_tools.analyze import analyze_sandbox
from src.tools.read_code import read_code
from src.tools.code_writer import write_code


load_dotenv()

def main():
    
    results = analyze_sandbox("./sandbox")
    for result in results:
        print(result)
    #code = read_code("sandbox/src/calculator.py")
    #print(code)
    #write_code("sandbox/src/calculator.py","# Ajout de cffffffffffffffffffffommentaire")

 
if __name__ == "__main__":
    main()     #! LES DEUX QUSTION  1.ASM LES FICHER IDA HWA 3TANA LES TEST 2. ASK HWA YRTINA LES TEST 