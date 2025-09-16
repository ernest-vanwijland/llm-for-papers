from api import *
from memory_util import *
import re

current_grades = {}
current_weights = {}

def grade(id, solutions, tree, VERIFIER):
    global current_grades, current_weights
    if id in current_grades.keys():
        return current_grades[id], current_weights[id]
    current_weights[id] = 0.0
    current_grades[id] = 1.0
    if tree.toprove[id] != -1:
        current_weights[id] += 1.0
        current_grades[id] += float(VERIFIER(tree, id, solutions[id]))
    for dep in tree.depends_on[id]:
        grd, wgt = grade(dep, solutions, tree, VERIFIER)
        current_weights[id] += wgt
        current_grades[id] += wgt * grd
    current_grades[id] /= current_weights[id]
    return current_grades[id], current_weights[id]

def weight(id, tree):
    if tree.toprove[id] == -1:
        return 0
    return 1.0

def grader(solutions, tree, VERIFIER):
    global current_grades, current_weights
    current_grades, current_weights = {}, {}















































