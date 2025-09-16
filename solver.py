from api import *
from memory_util import *
from tree import *

def solver_prompt(tree, id):
    rank = tree.ranking[id]
    can_use = [sid for sid in tree.ids if tree.ranking[sid] < rank]
    statement = get_problem_statement(tree.paper, tree.toprove[id])
    context = "\n".join([f"- {tree.name[sid]}" for sid in can_use])
    prompt = f"""
    ### List of statements you can assume to be already proved ###
    
    {context}
    
    ### Problem statement ###
    
    {tree.name[id]}:
    {statement}
    """
    return prompt

def geminiSolver(tree, id):
    return request([solver_prompt(tree, id)], system_prompt=solver_system_prompt, contents=[noproof(tree.paper)])

def gptSolver(tree, id):
    return openai_request(solver_prompt(tree, id), system_prompt=solver_system_prompt, paper = noproof(tree.paper))

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















































