from api import *
from memory_util import *
from tree import *

def solver_prompt(tree, id):
    rank = tree.ranking[id]
    can_use = [sid for sid in tree.ids if tree.ranking[sid] < rank]
    statement = get_problem_statement(tree.paper, tree.toprove[id])
    context = "\n".join([f"- {tree.name[sid]}" for sid in can_use])
    references = ""
    if len(tree.references[id]) > 0:
        references = f"""
    ### List of references you can use ###
        
    {tree.references[id]}
        
    """
    prompt = references + f"""
    ### List of statements you can assume to be already proved ###
    
    {context}
    
    ### Problem statement ###
    
    {tree.name[id]}:
    {statement}
    """
    return prompt

def correctSolver(tree, id):
    return get_proof(tree.paper, tree.toprove[id])

def geminiSolver(tree, id):
    return request(solver_prompt(tree, id), system_prompt=solver_system_prompt, files=[noproof(tree.paper)])

def gptSolver(tree, id):
    return openai_request(solver_prompt(tree, id), system_prompt=solver_system_prompt, paper = noproof(tree.paper))

def solver(tree, SOLVER):
    tree.print()
    solutions = {}
    levels = []
    for id in tree.ids:
        rank = tree.ranking[id]
        while len(levels) <= rank:
            levels.append([])
        levels[rank].append(id)
    for level in levels:
        for id in level:
            if tree.toprove[id] != -1:
                print(f"Currently solving {tree.paper}/{tree.name[id]} (TOPROVE {tree.toprove[id]}).")
                solutions[id] = SOLVER(tree, id)
    return solutions















































