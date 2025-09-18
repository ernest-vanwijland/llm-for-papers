from api import *
from memory_util import *
from verifier import *
from solver import *
from tree import *
import os
import glob
import concurrent.futures
from numpy import random
from test_util import *

def get_score(tree, grades):
    if not grades:
        return -1
    no_child = {}
    for id in tree.ids:
        no_child[id] = True
    for id in tree.ids:
        for parent in tree.depends_on[id]:
            no_child[parent] = False
    relevant = []
    for id, keep in no_child.items():
        if keep:
            relevant.append(id)
    no_weight = True
    total_weight = 0.0
    total_grade = 0.0
    #print(relevant)
    for id in relevant:
        if grades[id]["weight"] > 0.1:
            no_weight = False
            total_weight += grades[id]["weight"]
            total_grade += grades[id]["weight"] * grades[id]["grade"]
    if no_weight:
        return -1
    return total_grade / total_weight

def get_grades(filename):
    with open(f"results/{filename}", 'r', encoding='utf-8') as f:
        raw_grades = json.load(f)
    grades = {}
    for paper, raw_grades_paper in raw_grades.items():
        if paper == "timestamp":
            continue
        grades[paper] = {}
        for strid, vals in raw_grades_paper.items():
            grades[paper][int(strid)] = vals
    return grades

def get_solutions(filename):
    with open(f"results/{filename}", 'r', encoding='utf-8') as f:
        raw_solutions = json.load(f)
    solutions = {}
    for paper, raw_solutions_paper in raw_solutions.items():
        if paper == "timestamp":
            continue
        solutions[paper] = {}
        for strid, vals in raw_solutions_paper.items():
            solutions[paper][int(strid)] = vals
    return solutions

def present(trees, grades, name="tmp"):
    results = {}
    for paper, grades_paper in grades.items():
        if paper == "timestamp":
            continue
        tree = trees[paper]
        score = get_score(tree, grades_paper)
        if score < -0.1:
            continue
        results[paper] = score
    print(results)

def experiment(papers, name = "tmp"):
    if name == "tmp":
        name += f"_{str(random.randint(1, 10000))}"
    trees = build_trees_parallel(papers)
    solutions = run_solver_parallel(trees, name=name)
    grades = run_grader_parallel(trees, solutions, name=name)
    present(trees, grades, name=name)

if __name__ == "__main__":
    #experiment(["2502.09440"], name="2502.09440")
    #experiment(["2502.08125"], name="2502.08125")
    #experiment(["2502.09440", "2502.08125"])
    experiment(["2502.08328"], name="2502.08328")
    
    papers = os.listdir("data/")
    #experiment(papers, name = "full_experiment")
    
    















































