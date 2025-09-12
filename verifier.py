from api import *
from pipeline_util import *
from prompts import *

verifier_prompt = """
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

Verdict rule:

Assess whether the proof, as written, establishes the claim. Do not rewrite or “fix” the proof; only evaluate it.

You need to ouput just one number and nothing else, either 0 or 1. You need to output 0 if the proof is invalid in any way. If and only if the verdict says the proof is valid, output 1.

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
    
    raw_grade = request([prompt], system_prompt = system_prompt, contents = [full(paper)])

    if (raw_grade == None) or isinstance(raw_grade[0], str) or ((raw_grade.strip() not in ["0", "1"]) and (raw_grade[0] not in ["0", "1"]) and (int(raw_grade[0]) not in [0, 1])):
        print(raw_grade[0], raw_grade[0] not in [0, 1], raw_grade[0] not in ["0", "1"], raw_grade.strip() not in ["0", "1"], int(raw_grade[0]) not in [0, 1])
        print(f"Verifier returned invalid output: {raw_grade}")
        return -1
    
    grade = int(raw_grade[0])
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
