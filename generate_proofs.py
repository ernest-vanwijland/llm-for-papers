from pipeline import *
from pipeline_util import *
from api import *
from checker import *
import json

testcase_counter = 0
def save_testcase(paper, toprove, validity, comment, proof, name = None):
    if name == None:
        name = f"test/testcase_{testcase_counter}.json"
    else:
        name = f"test/{name}_{testcase_counter}.json"
    testcase_counter += 1
    testcase = {
        "paper": paper,
        "toprove": toprove,
        "validity": validity,
        "comment": comment,
        "proof": proof,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    try:
        with open(name, 'w', encoding='utf-8') as f:
            json.dump(testcase, f, indent=2, ensure_ascii=False)
        print(f"Memory saved to {name}")
        return True
    except Exception as e:
        print(f"Error saving memory to {name}: {e}")
        return False

def get_proof(paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    
    You are given an academic paper and one of the statements that appears in the paper. Your job is to return the proof of the statement as it appears in the paper, and nothing else. You will use latex for mathematical notations. You should provide the whole proof and make sure it is exactly the same as the one that appears in the paper. Sometimes, the proof might not be right after the statement in the paper.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx, memory_file)}
    """
    return request([prompt], contents = [full(paper)])

def paraphrase_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper. Your job is to rewrite the proof as a paraphrase in natural language while keeping every mathematical step and justification logically identical.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - Keep the same structure of claims and equations, but you may rephrase sentences.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

# @Julien : ici il faut ajouter toutes tes autres fonctions, si possible
# dans le meme format et avec le meme style que moi

def check_testcase(paper, toprove, validity, comment, proof):
    """ function that checks that the testcase is correct """
    # TODO

def generate_testcases(paper, idx, memory_file):
    proof = get_proof(paper, idx, memory_file)
    paraphrases = [paraphrase_proof(proof, paper, idx, memory_file) for _ in range(1)]
    # here add all the other modifications, correct and incorrect
    
    save_testcase(paper, idx, 1, "original", proof, f"original_{paper}_{idx}")
    for p in paraphrases:
        save_testcase(paper, idx, 1, "paraphrase", p, f"paraphrase_{paper}_{idx}")
    # do the same for the other modifications
    
    
















































