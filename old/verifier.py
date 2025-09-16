from api import *
from memory_util import *
import dspy
import os

lm = dspy.LM('openai/gpt-5', api_key=os.environ.get("OPENAI_API_KEY"), temperature=1.0, max_tokens=16000)
dspy.configure(lm=lm)

class Verify(dspy.Signature):
    #article_latex: str = dspy.InputField(desc="The full article as context.")
    statement: str = dspy.InputField()
    correct_proof: str = dspy.InputField()
    solution: str = dspy.InputField()
    valid: bool = dspy.OutputField(desc="You are a math proof checker. You are given a problem statement from a mathematics article, the correct proof of the statement and a candidate solution to solve that statement. Your job is to mark the solution as 'valid' if it is a valid proof of the statement. If the given solution follows the same logic as the correct solution and handles all the mentioned cases correctly, you need to mark it as 'valid'. If the solution is equivalent to the correct proof, you need to mark it as 'valid'. If some case is not handled or if the given solution is incomplete, you need to say it is not valid. Acceptance standard: Evaluate according to journal-level mathematical rigor—accept proofs only if they meet journal criteria (allowing literature-standard trivial omissions). You need to evaluate the solution in the context of where it should appear in the paper. If some steps are straightfoward, they don't need to be rigorously proved, but you need to check that they are valid. If some result is invoked from a part of the paper that was already proved in the context of where the current proof appears, you can fully reuse it without it being reproven here. You need to mark the solution as 'valid' only if it is fully valid. Else you need to mark is as invalid.")

dspy_verify = dspy.ChainOfThought(Verify)

def dspy_verifier(paper, idx, solution):
    f = open(f"data/{paper}/full.tex", "r")
    article_latex = f.read()
    statement = get_problem_statement(paper, idx)
    proof = get_proof(paper, idx)
    verdict = dspy_verify(statement = statement, correct_proof = proof, solution = solution)
    if verdict["valid"]:
        return 1
    else:
        return 0

verifier_prompt = """
You are a math proof checker.

## Input

- List of statements already proved that you can use in the context of where the current proof appears
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
    tree.print()
    print(tree.toprove[id])
    proof = get_proof(tree.paper, tree.toprove[id])
    rank = tree.ranking[id]
    print(rank)
    can_use = [sid for sid in tree.ids if tree.ranking[sid] < rank]
    statement = get_problem_statement(tree.paper, tree.toprove[id])
    context = "\n".join([f"- {tree.name[sid]}" for sid in can_use])
    prompt = f"""
    ### List of statements you can assume to be already proved ###
    
    {context}
    
    ### Correct solution ###
    
    {proof}
    
    ### Solution ###
    
    {solution}
    """
    
    print(prompt)
    
    raw_grade = request([prompt], system_prompt = verifier_prompt, contents = [full(tree.paper)])
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
















































