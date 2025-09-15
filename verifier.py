from api import *
from pipeline_util import *
from prompts import *
import dspy
import os

lm = dspy.LM('openai/gpt-5', api_key=os.environ.get("OPENAI_API_KEY"), temperature=1.0, max_tokens=16000)
dspy.configure(lm=lm)

class Verify(dspy.Signature):
    # article_latex: str = dspy.InputField()
    statement: str = dspy.InputField()
    correct_proof: str = dspy.InputField()
    solution: str = dspy.InputField()
    valid: bool = dspy.OutputField(desc="You are a math proof checker. You are given a problem statement from a mathematics article, the correct proof of the statement and a candidate solution to solve that statement. Your job is to mark the solution as 'valid' if it is a valid proof of the statement. If the given solution follows the same logic as the correct solution and handles all the mentioned cases correctly, you need to mark it as 'valid'. If the solution is equivalent to the correct proof, you need to mark it as 'valid'. If some case is not handled or if the given solution is incomplete, you need to say it is not valid. Acceptance standard: Evaluate according to journal-level mathematical rigor—accept proofs only if they meet jounral criteria (allowing literature-standard trivial omissions). You need to evaluate the solution in the context of where it should appear in the paper. If some steps are straightfoward, they don't need to be rigorously proved, but you need to check that they are valid. If some result is invoked from a part of the paper that was already proved in the context of where the current proof appears, you can fully reuse it without it being reproven here. You need to mark the solution as 'valid' only if it is fully valid. Else you need to mark is as invalid.")

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

verifier_prompt_old = """
You are a math proof checker.

INPUT:
- Problem statement
- Correct solution
- Solution
- Academic paper which contains the statement you need to prove in the context of where it appears in the paper.

If the given solution follows the same logic as the correct solution and handles all the mentioned cases correctly, you need to say it is valid. If some case is not handled or if the given solution is incomplete, you need to say it is invalid.

Acceptance standard: Evaluate according to ICALP-level mathematical rigor—accept proofs only if they meet ICALP’s criteria (allowing literature-standard trivial omissions)

You need to evaluate the proof in the context of where it should appear in the paper.

If some steps are straightfoward, they don't need to be rigorously proved, but you need to check that they are valid.

If some result is invoked from a part of the paper that was already proved in the context of where the current proof appears, you can fully reuse it without it being reproven here.

You need to ouput just one number and nothing else, either 0 or 1. You need to output 0 if the proof is invalid in any way. If and only if the proof is valid, output 1.
"""

verifier_prompt = """
You are a math proof checker.

INPUT:
- Problem statement
- Correct solution
- Solution

If the given solution follows the same logic as the correct solution and handles all the mentioned cases correctly, you need to say it is valid. If some case is not handled or if the given solution is incomplete, you need to say it is invalid.

Acceptance standard: Evaluate according to journal-level mathematical rigor—accept proofs only if they meet journal criteria (allowing literature-standard trivial omissions)

You need to evaluate the proof in the context of where it should appear in the paper.

If some steps are straightfoward, they don't need to be rigorously proved, but you need to check that they are valid.

If some result is invoked from a part of the paper that was already proved in the context of where the current proof appears, you can fully reuse it without it being reproven here.

You need to ouput just one number and nothing else, either 0 or 1. You need to output 0 if the proof is invalid in any way. If and only if the proof is valid, output 1.
"""

def verify(paper, idx, solution, system_prompt = verifier_prompt):
    statement = get_problem_statement(paper, idx)
    proof = get_proof(paper, idx)
    prompt = f"""
    ### Problem ###
    
    {statement}
    
    ### Correct solution ###
    
    {proof}
    
    ### Solution ###
    
    {solution}
    """
    
    raw_grade = request([prompt], system_prompt = verifier_prompt_old, contents = [full(paper)])
    #raw_grade = request([prompt], system_prompt = system_prompt, contents = [])
    
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
    
    return grade

def verifier(paper, idx, solution):
    values = [verify(paper, idx, solution) for _ in range(3)]
    cnt = [0, 0]
    for x in values:
        if x in [0, 1]:
            cnt[x] += 1
    if cnt[0] > cnt[1]:
        return 0
    return 1
