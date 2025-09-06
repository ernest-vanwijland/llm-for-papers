from pipeline import *
from pipeline_util import *
from api import *
from checker import *
import json
from prompts import verification_system_prompt, verification_reminder
import os

testcase_counter = 0
def save_testcase(paper, toprove, validity, comment, proof, name = None):
    global testcase_counter
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
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, 'w', encoding='utf-8') as f:
            json.dump(testcase, f, indent=2, ensure_ascii=False)
        print(f"Memory saved to {name}")
        return True
    except Exception as e:
        print(f"Error saving memory to {name}: {e}")
        return False

def load_original_proof(paper, idx, cache_dir="test"):
    """Return any cached 'original' proof for (paper, idx) from test/*.json, or None"""
    if not os.path.isdir(cache_dir):
        return None
    for name in os.listdir(cache_dir):
        if not name.endswith(".json"):
            continue
        path = os.path.join(cache_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if data.get("paper") == paper and data.get("toprove") == idx and data.get("comment") == "original":
            return data.get("proof")
    return None

def get_proof(paper, idx):
    cached = get_original_proof(paper, idx)
    if isinstance(cached, str) and cached.strip():
        print("load cached proof")
        return cached, False
    prompt = f"""
    ### Instructions ###
    
    You are given an academic paper and one of the statements that appears in the paper. Your job is to return the proof of the statement as it appears in the paper, and nothing else. You will use latex for mathematical notations. You should provide the whole proof and make sure it is exactly the same as the one that appears in the paper. Sometimes, the proof might not be right after the statement in the paper.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    """
    return request([prompt], contents = [full(paper)]), True

def paraphrase_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to rewrite the proof as a paraphrase in natural language while keeping every mathematical step and justification logically identical.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - Keep the same structure of claims and equations, but you may rephrase sentences.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def rename_vars_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to consistently rename variables and symbols throughout the proof (e.g., $x \\to u$, $S \\to T$) without changing the logic.
        Constraints:
        - Preserve correctness rigorously.
        - Keep LaTeX notation consistent across the proof.
        - DO NOT change any mathematical content or the ordering of logically dependent steps.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def reorder_noncritical_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to reorder independent steps or cases in the proof (e.g., present Case 2 before Case 1) without changing dependencies or the logical content.
        Constraints:
        - DO NOT move a step before its prerequisites.
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def expand_justifications_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to expand terse parts of the proof by inserting short, rigorous justifications for steps that were previously implicit.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - Add only the minimal explanations necessary to clarify implicit steps.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def compress_justifications_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to compress the proof by removing redundant commentary while preserving all logically necessary steps.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - DO NOT remove logically necessary steps.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

# --- invalidating edits ---

def drop_key_step_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to remove exactly one logically essential step so the proof contains a fatal gap but remains superficially plausible.
        Constraints:
        - DO NOT add new arguments that would repair the gap.
        - Keep the rest of the proof intact and plausible.
        - Ensure the resulting proof is invalid.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def wrong_bound_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to introduce a subtle but fatal inequality or constant error (e.g., replace $\le$ by $<$ or alter a constant) so the proof becomes invalid.
        Constraints:
        - Keep the rest of the proof unchanged and plausible.
        - Ensure the resulting proof is invalid.
        - Make only a minimal change that causes the flaw.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def weaken_assumption_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper. 
    Your job is to remove or weaken a critical assumption right before it is used so that an application of a lemma/theorem becomes unjustified and the proof becomes invalid.
        Constraints:
        - Keep the narrative smooth and plausible.
        - Ensure the resulting proof is invalid.
        - Change only the assumption usage; do not add new valid arguments.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def quantifier_swap_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper. Your job is to alter the order or scope of quantifiers in a key step (swap $\\forall$ and $\\exists$ improperly) to create a fatal logical flaw.
        Constraints:
        - Keep the rest of the proof as intact as possible.
        - Ensure the resulting proof is invalid.
        - Make the change subtle but decisive.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def case_mismerge_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper. 
    Your job is to mishandle or omit one necessary case in the case analysis so that the conclusion becomes invalid.
        Constraints:
        - Keep the text plausible.
        - Ensure the resulting proof is invalid.
        - Do not introduce new correct arguments that close the gap.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

def circular_reasoning_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to introduce circular reasoning by using the statement being proved (or an equivalent) as justification for a step, making the proof invalid.
        Constraints:
        - Keep the text plausible.
        - Ensure the resulting proof is invalid.
        - Make the circularity subtle but present.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])



















































