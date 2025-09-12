from api import *
from memory_util import *
from generate_proofs import *
from verifier import *
from presentation import *
import os
import glob
import multiprocessing
import concurrent.futures

one_proof = {
    "2407.02412": [1]
}

ten_proofs = {
    "2502.08328": [31, 32, 33, 34, 35],
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

def run_checker(testcases, CHECKER):
    results = {}
    testcase_files = glob.glob(f"test/{testcases}/*")
    nb_testcases = len(testcase_files)
    cnt = 1
    for testcase_file in testcase_files:
        print(f"Running checker on {testcase_file} ({cnt} of {nb_testcases})")
        cnt += 1
        testcase = load_testcase(testcase_file)
        if testcase == None:
            continue
        results[testcase_file] = CHECKER(testcase["paper"], testcase["toprove"], testcase["proof"])
    return results

def run_and_collect_result(testcase_file, CHECKER, results):
    """
    Worker function to run the checker on a single testcase file and store the result.
    """
    print(f"Running checker on {testcase_file}")
    testcase = load_testcase(testcase_file)
    if testcase:
        results[testcase_file] = CHECKER(testcase["paper"], testcase["toprove"], testcase["proof"])

def run_checker_parallel(testcases, CHECKER, num_processes=50):
    """
    Runs the checker in parallel for all test cases in a given folder, using a semaphore.
    """
    manager = multiprocessing.Manager()
    results = manager.dict()
    testcase_files = glob.glob(f"test/{testcases}/*")
    semaphore = multiprocessing.Semaphore(num_processes)
    processes = []

    def worker(testcase_file, CHECKER, results_dict):
        try:
            run_and_collect_result(testcase_file, CHECKER, results_dict)
        finally:
            semaphore.release()

    for testcase_file in testcase_files:
        semaphore.acquire()
        process = multiprocessing.Process(target=worker, args=(testcase_file, CHECKER, results))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("All parallel checker tasks completed.")
    return dict(results)

def run_checker_on_specific(testcases, CHECKER, paper, indices):
    results = {}
    all_testcase_files = glob.glob(f"test/{testcases}/*")
    
    filtered_files = []
    for testcase_file in all_testcase_files:
        testcase = load_testcase(testcase_file)
        if testcase is None:
            continue

        if testcase.get("paper") == paper and testcase.get("toprove") in indices:
            filtered_files.append(testcase_file)

    if not filtered_files:
        print(f"No testcases found for paper {paper} and TOPROVE {indices}")
        return results

    for testcase_file in filtered_files:
        filename, result = run_checker_on_file(testcase_file, CHECKER)
        if result is not None:
            results[filename] = result
            
    return results

def save_results(results, results_file):
    results_file = f"results/{results_file}"
    print(f"Saving results to {results_file}")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def run_and_save(args):
    """
    Worker function to run the checker on a single TOPROVE and save the result.
    """
    print(f"--- Starting task with args: {args} ---")
    paper, idx, CHECKER, testcases = args
    checker_name = CHECKER.__name__
    print(f"--- Starting check for paper {paper}, TOPROVE {idx} with {checker_name} ---")
    results = run_checker_on_specific(testcases, CHECKER, paper=paper, indices=[idx])
    save_results(results, f"results_{paper}_{idx}_{checker_name}.json")
    print(f"--- Finished check for paper {paper}, TOPROVE {idx} ---")

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

def run_full_parallel(papers_and_proofs, testcases, CHECKER, max_workers=60):
    """
    Runs the checker in parallel for all relevant test cases using a thread pool.
    :param max_workers: The maximum number of threads to run at once. Defaults to 60.
    """
    all_testcase_files = glob.glob(f"test/{testcases}/*")
    
    # Filter files based on papers_and_proofs
    tasks = []
    for testcase_file in all_testcase_files:
        testcase = load_testcase(testcase_file)
        if testcase and testcase.get("paper") in papers_and_proofs and testcase.get("toprove") in papers_and_proofs[testcase.get("paper")]:
            tasks.append(testcase_file)
    print(f"Starting parallel processing with {len(tasks)} processes...{tasks} ")
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

def run_parallel(papers_and_proofs, testcases, CHECKER):
    tasks = []
    for paper, toprove in papers_and_proofs.items():
        for idx in toprove:
            print(f"Preparing task for paper {paper}, TOPROVE {idx}")
            tasks.append((paper, idx, CHECKER, testcases))
    print(os.cpu_count())
    num_processes = min(len(tasks), os.cpu_count() or 1)
    print(f"Starting parallel processing with {num_processes} processes...")
    with multiprocessing.Pool(processes = num_processes) as pool:
        pool.map(run_and_save, tasks)
    print("All parallel tasks completed.")

if __name__ == "__main__":
    #prepare_testcases(one_proof, "one_proof", 0)
    # results = run_checker("one_proof", checker)
    #save_results(results, "results_one_proof.json")
    
    #prepare_testcases(ten_proofs, "ten_proofs", 0)
    
    #print(get_nb_proofs(hundred_proofs))
    
    proof = {
        "2502.09440": [1]
    }
    # run_parallel(ten_proofs, "ten_proofs", verify)
    run_full_parallel(ten_proofs, "ten_proofs", verifier)
    compile_results(verifier)

    
    
    #compile_results(checker)
    #compile_results(checker_lv1)
    #compile_results(checker_lv2)
    #compile_results(checker_lv3_adv)
    #compile_results(majority_nicer)
    # compile_results(verifier)















































