from api import *
from memory_util import *
from generate_proofs import *
from verifier import *
from presentation import *
import os
import glob
import multiprocessing
import concurrent.futures
from numpy import random
from test_util import *

icalp25 = {
    "2502.09440": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "2502.08328": [11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34],
    "2410.09321": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "2502.08125": [0, 1, 2, 3, 4, 5, 6, 7]
}

def experiment(papers_and_proofs, testfolder):
    generate_parallel(papers_and_proofs, testfolder)
    verify_parallel(papers_and_proofs, testfolder, dspy_verifier)
    compile_results(dspy_verifier)

if __name__ == "__main__":
    #prepare_testcases(one_proof, "one_proof", 0)
    
    # 1. Testcase generation
    #generate_parallel(icalp25, "icalp25")
    
    # 2. Verification
    #verify_parallel(icalp25, "icalp25", dspy_verifier)
    
    # 3. Presentation
    compile_results(dspy_verifier)
    
    















































