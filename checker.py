from api import *
from pipeline_util import *
from prompts import *

def verify_solution(paper, idx, memory_file):
    memory = load_memory(memory_file)
    statement = get_problem_statement(paper, idx, memory_file)
    solution = extract_detailed_solution(get_solution(idx, memory))
    prompt = f"""
    ### Problem ###
    
    {statement}
    
    ### Solution ###
    
    {solution}
    
    {verification_reminder}
    """
    
    detailed_verif = request([prompt], system_prompt = verification_system_prompt, contents = [full(paper)])
    
    prompt = f"""
    ### Instructions ###
    
    You are given a detailed verification log of a mathematical proof, with a verdict on its validity. You need to ouput just one number and nothing else, either 0 or 1. You need to output 0 if the proof is invalid or incomplete in any way. If and only if the verdict says the proof is completely correct, output 1.
    
    ### Verification log: ###
    
    {detailed_verif}
    """
    
    grade = int(request([prompt], contents = []))
    
    save_verif(idx, detailed_verif, memory)
    save_grade(idx, grade, memory)
    save_memory(memory_file, memory)
    
    return detailed_verif, grade

def grade_once(paper, idx, memory):
    prompt = f"### Task ###\nYour task is to verify that \n------\n{memory['solutions'][idx]}\n-----\nis a valid proof of {memory['statements'][idx]}\n in the context of where the statement and its proof appear in the attached paper.\n"
    prompt += "You can use the paper and understand the actual correct proof of the statement in the paper to get a deeper understanding of the subtelties of the problem you are tackling and provide a more thorough verification."
    paper = full(paper)
    detailed_verif = request([prompt], system_prompt = verification_system_prompt, contents = [paper])
    prompt = "### Instructions ###\n You are given a detailed verification log of a mathematical proof, with a verdict on its validity. You need to ouput just one number and nothing else, either 0 or 1. You need to output 0 if the proof is invalid or incomplete in any way. If and only if the verdict says the proof is completely correct, output 1.\n ### Here comes the verification log: ###\n"
    prompt += detailed_verif
    grade = int(request([prompt], contents=[]))
    return grade
   
def grade_idx(paper, idx, memory, nbVerifs = 1):
    grade = 0
    for _ in range(nbVerifs):
        grade += grade_once(paper, idx, memory)
    # grade = 1 iff all the verifications are correct
    grade //= nbVerifs
    return grade

def grade(paper, memory_file):
    memory = load_memory(memory_file)
    nbProofs = min(len(memory["statements"]), len(memory["solutions"]))
    total = 0
    correct = 0
    for idx in range(nbProofs):
        if memory["statements"][idx] != None:
            total += 1
            correct += grade_idx(paper, idx, memory)
    if total == 0:
        return None
    return correct, total
