from api import *
from memory_util import *
import dspy
import os

verifier_prompt = """
You are a math proof checker.

## Input

- List of statements already proved that you can use in the context of where the current proof appears
- (Optional): List of external references that can be reused
- Problem statement
- Correct solution
- Solution
- Academic paper

## Core Instructions

You need to decide if the given solution is a valid proof of the problem statement in the context of where it appears in the given paper.

If the given solution follows the same logic as the correct solution and handles all the mentioned cases correctly, you need to say it is valid. If some case is not handled or if the given solution is incomplete, you need to say it is invalid.

Acceptance standard: Evaluate according to journal-level mathematical rigor—accept proofs only if they meet journal criteria (allowing literature-standard trivial omissions).

You need to evaluate the proof in the context of where it should appear in the paper, the solution can fully assume the given list of statements as already proved. If some result that is not in the list in invoked but not proved, you need to mark the solution as invalid.

If some steps are straightfoward, they don't need to be rigorously proved, but you need to check that they are valid.

## Output Format

The output MUST be a single integer, either 0 if the solution is invalid or 1 if it is valid. Do not include any text, explanations, or formatting before or after the integer.
"""

def verifier(tree, id, solution):
    proof = get_proof(tree.paper, tree.toprove[id])
    rank = tree.ranking[id]
    #print(rank)
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
    
    ### Correct solution ###
    
    {proof}
    
    ### Solution ###
    
    {solution}
    """
    
    #print(prompt)
    
    raw_grade = request(prompt, system_prompt = verifier_prompt, files = [full(tree.paper)])
    #raw_grade = openai_request(prompt, system_prompt = verifier_prompt, paper = full(tree.paper))
    
    if raw_grade == None:
        print("Hey")
        return -1
    elif raw_grade[0] in ['0', '1']:
        return int(raw_grade[0])
    elif raw_grade[-1] in ['0', '1']:
        return int(raw_grade[-1])
    else:
        print(f"Verifier returned invalid output: {raw_grade}")
        return -1

def majority_verifier(tree, id, solution):
    grades = [verifier(tree, id, solution) for _ in range(3)]
    cnt = [0, 0]
    for g in grades:
        if g in [0, 1]:
            cnt[g] += 1
    if cnt[0] > cnt[1]:
        return 0
    return 1

def max_verifier(tree, id, solution):
    grades = [verifier(tree, id, solution) for _ in range(3)]
    return max(grades)















































