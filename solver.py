from api import *
from memory_util import*

def solver_prompt(paper, idx):
    statement = get_problem_statement(paper, idx)
    prompt = f"""
    ### Problem statement ###
    
    {statement}
    """
    return prompt

def geminiSolver(paper, idx):
    return request([solver_prompt(paper, idx)], system_prompt=solver_system_prompt, contents = [noproof(paper)])

def gptSolver(paper, idx):
    return openai_request(solver_prompt(paper, idx), system_prompt=solver_system_prompt, paper = noproof(paper))















































