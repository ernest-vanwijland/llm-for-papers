from api import *
from memory_util import *
from verifier import *
import re

def grade(id, solutions, tree, VERIFIER, current_grades, current_weights):
    if id in current_grades.keys():
        return current_grades[id], current_weights[id]
    current_weights[id] = 0.0
    current_grades[id] = 0.0
    if tree.toprove[id] != -1:
        current_weights[id] += 1.0
        print(f"Currently verifying {tree.paper}/{tree.name[id]} (TOPROVE {tree.toprove[id]}).")
        current_grades[id] += float(VERIFIER(tree, id, solutions[id]))
    for dep in tree.depends_on[id]:
        grd, wgt = grade(dep, solutions, tree, VERIFIER, current_grades, current_weights)
        current_weights[id] += wgt
        current_grades[id] += wgt * grd
    if current_weights[id] > 0.1:
        current_grades[id] /= current_weights[id]
    return current_grades[id], current_weights[id]

def weight(id, tree):
    if tree.toprove[id] == -1:
        return 0
    return 1.0

def grader(solutions, tree, VERIFIER):
    current_grades, current_weights = {}, {}
    grades = {}
    for id in tree.ids:
        grd, wgt = grade(id, solutions, tree, VERIFIER, current_grades, current_weights)
        grades[id] = {
            "grade": grd,
            "weight": wgt
        }
    return grades















































