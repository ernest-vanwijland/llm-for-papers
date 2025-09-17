from api import *
from memory_util import *
from grader import *
from solver import *
from verifier import *
from tree import *
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
        tree = Tree(testcase["paper"])
        id = get_id(tree, testcase["toprove"])
        result = CHECKER(tree, id, testcase["proof"])
        return testcase_file, result
    return testcase_file, None

def build_tree(paper):
    return paper, Tree(paper)

def run_solver(tree):
    return tree.paper, solver(tree, geminiSolver)

def run_grader(tree, solutions):
    return tree.paper, grader(solutions, tree, verifier)

def run_solver_parallel(trees, name = "tmp", max_workers = 100):
    print(f"Starting parallel solving on {len(trees.keys())} DAGs with {max_workers} workers.")
    solutions = {}
    for paper, tree in trees.items():
        solutions[paper] = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {executor.submit(run_solver, tree): paper for paper, tree in trees.items()}
        for future in concurrent.futures.as_completed(future_to_paper):
            pap = future_to_paper[future]
            try:
                paper, solutions_paper = future.result()
                if solutions_paper is not None:
                    solutions[paper] = solutions_paper
                with open(f"results/solutions_{name}.json", 'w', encoding='utf-8') as f:
                    json.dump(solutions, f, indent=2, ensure_ascii=False)
            except Exception as exc:
                print(f'{pap} generated an exception: {exc}')
    print(f"Saving solutions to results/solutions_{name}.json.")
    solutions["timestamp"] = __import__('datetime').datetime.now().isoformat()
    with open(f"results/solutions_{name}.json", 'w', encoding='utf-8') as f:
        json.dump(solutions, f, indent=2, ensure_ascii=False)
    return solutions

def run_grader_parallel(trees, solutions, name = "tmp", max_workers = 100):
    tasks = []
    for paper, tree in trees.items():
        if solutions[paper]:
            tasks.append((tree, solutions[tree.paper]))
    grades = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_paper = {executor.submit(run_grader, tree, solutions_tree): tree.paper for tree, solutions_tree in tasks}
        for future in concurrent.futures.as_completed(future_to_paper):
            pap = future_to_paper[future]
            try:
                paper, grades_paper = future.result()
                if grades_paper is not None:
                    grades[paper] = grades_paper
                with open(f"results/grades_{name}.json", 'w', encoding='utf-8') as f:
                    json.dump(grades, f, indent=2, ensure_ascii=False)
            except Exception as exc:
                print(f'{pap} generated an exception: {exc}')
    print(f"Saving grades to results/grades_{name}.json.")
    grades["timestamp"] = __import__('datetime').datetime.now().isoformat()
    with open(f"results/grades_{name}.json", 'w', encoding='utf-8') as f:
        json.dump(grades, f, indent=2, ensure_ascii=False)
    return grades

def build_trees_parallel(papers, max_workers = 100):
    print(f"Starting parallel building on {len(papers)} papers with {max_workers} workers.")
    trees = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_tree = {executor.submit(build_tree, paper): paper for paper in papers}
        for future in concurrent.futures.as_completed(future_to_tree):
            pap = future_to_tree[future]
            try:
                paper, tree = future.result()
                if tree is not None:
                    trees[paper] = tree
            except Exception as exc:
                print(f'{pap} generated an exception: {exc}')
    return trees

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
    
    















































