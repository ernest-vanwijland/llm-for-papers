from api import *
from memory_util import *
from tree import *

def solver_prompt(paper, idx):
    statement = get_problem_statement(paper, idx)
    prompt = f"""
    ### Problem statement ###
    
    {tree.name[id]}:
    {statement}
    """
    return prompt

def geminiSolver(paper, idx):
    return request([solver_prompt(paper, idx)], system_prompt=solver_system_prompt, contents = [noproof(paper)])

def gptSolver(paper, idx):
    return openai_request(solver_prompt(paper, idx), system_prompt=solver_system_prompt, paper = noproof(paper))

def solver(tree, SOLVER):
    solutions = {}
    levels = []
    for id in tree.ids:
        rank = tree.ranking[id]
        while len(levels) <= rank:
            levels.append([])
        levels[rank].append(id)
    for level in range(levels):
        for id in level:
            if tree.toprove[id] != -1:
                solutions[id] = SOLVER(tree, id)















































