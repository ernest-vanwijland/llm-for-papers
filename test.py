from api import *
from memory_util import *
from generate_proofs import *
from checker import *
import os
import glob

one_proof = {
    "2407.02412": [1]
}

ten_proofs = {
    "2502.08328": [],
    "2502.09440": [1, 2, 3, 4, 5]
}

hundred_proofs = {
    "2502.09440": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "2502.08328": [11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 35]
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

def run_checker(subfolder):
    results = {}
    testcase_files = glob.glob(f"test/{subfolder}/*")
    nb_testcases = len(testcase_files)
    cnt = 1
    for testcase_file in testcase_files:
        print(f"Running checker on {testcase_file} ({cnt} of {nb_testcases})")
        cnt += 1
        testcase = load_testcase(testcase_file)
        if testcase == None:
            continue
        results[testcase_file] = checker(testcase["paper"], testcase["toprove"], testcase["proof"])
    return results

def save_results(results, results_file):
    results_file = f"results/{results_file}"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    #prepare_testcases(one_proof, "one_proof", 0)
    #results = run_checker("one_proof")
    #save_results(results, "results_one_proof.json")
    
    # prepare_testcases(ten_proofs, "ten_proofs", 0)
    
    print(get_nb_proofs(hundred_proofs))

















































