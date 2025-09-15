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

one_proof = {
    "2407.02412": [1]
}

ten_proofs = {
    "2502.08328": [31, 32, 33, 34],
    "2502.09440": [1, 2, 3, 4, 5]
}

hundred_proofs = {
    "2502.09440": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "2502.08328": [11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34]
}

def get_nb_proofs(proofs):
    cnt = 0
    for paper, toprove in proofs.items():
        for idx in toprove:
            cnt += 1
    return cnt

def get_all_proofs(proofs):
    cnt = 1
    for paper, toprove in proofs.items():
        for idx in toprove:
            print(f"Retrieving proof {paper}/{idx} ({cnt} of {get_nb_proofs(proofs)})")
            get_proof(paper, idx)
            cnt += 1

def generate_all_testcases(proofs, subfolder, nb_variants):
    os.makedirs(f"test/{subfolder}", exist_ok=True)
    cnt = 1
    for paper, toprove in proofs.items():
        for idx in toprove:
            print(f"Generating variants of proof {paper}/{idx} ({cnt} of {get_nb_proofs(proofs)})")
            generate_testcases(paper, idx, subfolder, nb_variants)
            cnt += 1

def prepare_testcases(proofs, subfolder, nb_variants = 1):
    get_all_proofs(proofs)
    generate_all_testcases(proofs, subfolder, nb_variants)

def load_testcase(testcase_file):
    if not os.path.exists(testcase_file):           
        return None
    try:
        with open(testcase_file, 'r', encoding='utf-8') as f:
            testcase = json.load(f)
        # print(f"Memory loaded from {memory_file}")
        return testcase
    except Exception as e:
        #print(f"Error loading testcase from {testcase_file}: {e}")
        return None

def save_results(results, results_file):
    results_file = f"results/{results_file}"
    print(f"Saving results to {results_file}")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def run_checker_on_file(testcase_file, CHECKER):
    """
    Worker function to run the checker on a single testcase file.
    """
    print(f"Running checker on {testcase_file}")
    testcase = load_testcase(testcase_file)
    if testcase:
        result = CHECKER(testcase["paper"], testcase["toprove"], testcase["proof"])
        return testcase_file, result
    return testcase_file, None

def generate_parallel(proofs, subfolder, max_workers=100):
    """
    Generates testcases in parallel for all relevant proofs using a thread pool.
    """
    tasks = []
    for paper, toprove in proofs.items():
        for idx in toprove:
            tasks.append((paper, idx))
    random.shuffle(tasks)
    print(f"Starting parallel generation on {len(tasks)} proofs with {max_workers} workers.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(generate_testcases, paper, idx, subfolder, 1): (paper, idx) for (paper, idx) in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            paper, idx = future_to_task[future]
            print(f"Done generating testcases for {paper}/{idx}.")
    print("Done generating all testcases.")

def verify_parallel(papers_and_proofs, testcases, CHECKER, max_workers=100):
    """
    Runs the checker in parallel for all relevant test cases using a thread pool.
    """
    all_testcase_files = glob.glob(f"test/{testcases}/*")
    
    # Filter files based on papers_and_proofs
    tasks = []
    for testcase_file in all_testcase_files:
        testcase = load_testcase(testcase_file)
        if testcase and testcase.get("paper") in papers_and_proofs and testcase.get("toprove") in papers_and_proofs[testcase.get("paper")]:
            tasks.append(testcase_file)
    random.shuffle(tasks)
    print(f"Starting parallel processing on {len(tasks)} testcases with {max_workers} workers.")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(run_checker_on_file, file, CHECKER): file for file in tasks}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                filename, result = future.result()
                if result is not None:
                    results[filename] = result
            except Exception as exc:
                print(f'{file} generated an exception: {exc}')

    checker_name = CHECKER.__name__
    save_results(results, f"results_{testcases}_{checker_name}.json")
    print("All parallel tasks completed.")
    
    















































