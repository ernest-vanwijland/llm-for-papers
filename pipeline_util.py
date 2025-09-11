from api import *
from prompts import *
from memory_util import *
from prompts import *
import json
import os

def load_problem_statements(paper):
    idx = 0
    while get_problem_statement(paper, idx) != "NONE" and idx < 100:
        idx += 1
    if idx == 100:
        print("Too many TOPROVE, there must be a problem.")
    return idx





































