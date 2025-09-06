from api import *
from pipeline_util import *
from checker import *
from prompts import *

def first_attempt(paper, idx):
    paper = noproof(paper)
    statement = get_problem_statement(paper, idx)
    prompt = f"""
    Your job is to prove:
    --- BEGIN STATEMENT ---
    {statement}
    --- END STATEMENT ---
    in the context of where TOPROVE {idx} appears in the attached paper. You can only use the results that where assumed or already proved at this point in the paper (notably you can assume all the previous TOPROVE where proved) as well as the references attached, and your own reasonning. You cannot use any result that is proved later in the paper or invent any lemma.
    """
    
    solution = request([prompt], system_prompt = step1_prompt, contents = [paper])
    save_solution(paper, idx, solution)
    return solution

def self_improvement(paper, idx, verif = None):
    first_solution = get_solution(paper, idx)
    statement = get_problem_statement(paper, idx)
    if verif:
        solution = request([statement, correction_prompt, verif], system_prompt = step1_prompt, model = first_solution, contents = [paper])
    else:
        solution = request([statement, self_improvement_prompt], system_prompt = step1_prompt, model = first_solution, contents = [noproof(paper)])
    save_solution(paper, idx, solution)
    return solution

def solve(paper, idx):
    first_attempt(paper, idx)
    solution = self_improvement(paper, idx)
    detailed_verif, grade = verify_solution(paper, idx)
    error_count = 0
    correct_count = 1
    success = False
    nbIterations = 30
    for i in range(30):
        print(f"#iterations: {i}, #correct: {correct_count}, #error: {error_count}")
        if grade == 0:
            correct_count = 0
            error_count += 1
            solution = self_improvement(paper, idx, detailed_verif)
        
        detailed_verif, grade = verify_solution(paper, idx)
        
        if grade == 1:
            correct_count += 1
            error_count = 0
        
        if correct_count >= 5:
            return solution
        elif error_count >= 10:
            return None
    
    if not success:
        return None

if __name__ == "__main__":
    papers = list_papers("data/")
    
    paper = "2407.02412"
    
    #verify_solution(paper, 0)
    
    print(get_problem_statement(paper, 3))





























































