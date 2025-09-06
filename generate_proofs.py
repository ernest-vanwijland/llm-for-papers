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
    
def _load_cached_proof_from_testdir(paper, idx, cache_dir="test"):
    """Return any cached 'original' proof for (paper, idx) from test/*.json, or None (no recency logic).."""
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


def get_proof(paper, idx, memory_file):
    cached = _load_cached_proof_from_testdir(paper, idx)
    if isinstance(cached, str) and cached.strip():
        print("load cached proof")
        return cached, False
    prompt = f"""
    ### Instructions ###
    
    You are given an academic paper and one of the statements that appears in the paper. Your job is to return the proof of the statement as it appears in the paper, and nothing else. You will use latex for mathematical notations. You should provide the whole proof and make sure it is exactly the same as the one that appears in the paper. Sometimes, the proof might not be right after the statement in the paper.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx, memory_file)}
    """
    return request([prompt], contents = [full(paper)]), True

def paraphrase_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def rename_vars_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def reorder_noncritical_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def expand_justifications_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def compress_justifications_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
# --- invalidating edits ---

def drop_key_step_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def wrong_bound_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def weaken_assumption_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def quantifier_swap_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper. Your job is to alter the order or scope of quantifiers in a key step (swap $\\forall$ and $\\exists$ improperly) to create a fatal logical flaw.
        Constraints:
        - Keep the rest of the proof as intact as possible.
        - Ensure the resulting proof is invalid.
        - Make the change subtle but decisive.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def case_mismerge_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
def circular_reasoning_proof(proof, paper, idx, memory_file):
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
    
    {get_problem_statement(paper, idx, memory_file)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])
# @Julien : ici il faut ajouter toutes tes autres fonctions, si possible
# dans le meme format et avec le meme style que moi
def verify_solution_not_in_memory(paper, idx, memory_file, solution):

    statement = get_problem_statement(paper, idx, memory_file)
    print("statement", statement)
    print("solution", solution)
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
    
    
    return detailed_verif, grade

_ALLOWED_REASON_LABELS = [
    "valid",
    "drop_key_step",
    "wrong_bound",
    "weaken_assumption",
    "quantifier_swap",
    "case_mismerge",
    "circular_reasoning",
    "unknown"
]

def _normalize_reason_llm(details: str, is_valid: int|None) -> str:
   
    fallback = "valid" if is_valid == 1 else "unknown"
    if not isinstance(details, str) or not details.strip():
        return fallback
    labels = ", ".join(_ALLOWED_REASON_LABELS)
    prompt = f"""
    ### Instructions ###
    You are given a short diagnostic note about whether a mathematical proof is valid or why it is invalid.
    Map the note to exactly ONE label from: {labels}.
        Constraints:
        - If the proof is correct, output: valid
        - Otherwise choose the most specific error:
          - drop_key_step (missing essential step / fatal gap)
          - wrong_bound (inequality/bound/constant is wrong; ≤ vs <, etc.)
          - weaken_assumption (required hypothesis missing/weakened; unjustified lemma)
          - quantifier_swap (∀/∃ order/scope issue)
          - case_mismerge (case analysis missing/incorrect/non-exhaustive)
          - circular_reasoning (uses the claim itself / begs the question)
          - unknown (none of the above / unclear)
        - Output EXACTLY one label, lowercase, no punctuation, no extra text.

    ### Diagnostic note ###

    {details}
    """
    print("LLM normalizing reason with prompt:")
    res = request([prompt], contents=[])

    label = res.strip().split()[0].lower()
    return label if label in _ALLOWED_REASON_LABELS else fallback
    

def check_testcase(paper, toprove, expected_validity, expected_reason, proof, memory_file):
    """ function that checks that the testcase is correct """

    print("Checking testcase:", paper, toprove, expected_validity, expected_reason)
    detailed_verif, grade = verify_solution_not_in_memory(paper, toprove, memory_file, proof)
    print("verify pass")
    validity_ok = grade == expected_validity
    print("validity ok:", validity_ok)
    # 3) Trouver la raison
    found_reason = _normalize_reason_llm(detailed_verif, grade)
    print("found reason pass")
    # 4) Comparer validité et raison
    
    reason_ok = (expected_reason is None) or (grade == 1 and expected_reason == "valid") or (found_reason == expected_reason)

    return {
        "paper": paper,
        "idx": toprove,
        "expected_validity": expected_validity,
        "found_validity": grade,
        "validity_ok": validity_ok,
        "expected_reason": expected_reason,
        "found_reason": found_reason,
        "reason_ok": reason_ok,
        "details": detailed_verif
    }

def save_checked_variants(paper, idx, variants, expected_validity, method_label, memory_file):

    expected_reason = "valid" if expected_validity == 1 else method_label

    saved = 0
    for v in variants:
        print("check")
        res = check_testcase(paper, idx, expected_validity, expected_reason, v, memory_file)
        if res["validity_ok"] and res["reason_ok"]:
            ok = save_testcase(paper, idx, expected_validity, method_label, v, f"{paper}_{idx}_{method_label}")
            if ok:
                saved += 1
        else:
            print(f"Skipped saving {method_label} due to failed check:", res)
    return saved

def generate_testcases(paper, idx, memory_file, nb_variants=1):
    proof,is_new = get_proof(paper, idx, memory_file)
    if is_new:
        save_testcase(paper, idx, 1, "original", proof, f"{paper}_{idx}_original")
    res_sanitary = save_checked_variants(paper, idx, [proof],                   1, "sanitary_check", memory_file)
    print("res_sanitary", res_sanitary)
    # ------- verification -------
    paraphrases = [paraphrase_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    res0 = save_checked_variants(paper, idx, paraphrases,                   1, "paraphrase", memory_file)
    print("res0", res0)

    # rename_vars_proofs = [rename_vars_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res1 = save_checked_variants(paper, idx, rename_vars_proofs,            1, "rename_vars", memory_file)
    # print("res1", res1)

    # reorder_noncritical_proofs = [reorder_noncritical_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res2 = save_checked_variants(paper, idx, reorder_noncritical_proofs,    1, "reorder_noncritical", memory_file)
    # print("res2", res2)

    # expand_justifications_proofs = [expand_justifications_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res3 = save_checked_variants(paper, idx, expand_justifications_proofs,  1, "expand_justifications", memory_file)
    # print("res3", res3)

    # compress_justifications_proofs = [compress_justifications_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res4 = save_checked_variants(paper, idx, compress_justifications_proofs,1, "compress_justifications", memory_file)
    # print("res4", res4)
    # ------- falsification --------
    drop_key_step_proofs = [drop_key_step_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    res5 = save_checked_variants(paper, idx, drop_key_step_proofs,          0, "drop_key_step", memory_file)
    print("res5", res5)

    # wrong_bound_proofs = [wrong_bound_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res6 = save_checked_variants(paper, idx, wrong_bound_proofs,            0, "wrong_bound", memory_file)
    # print("res6", res6)

    # weaken_assumption_proofs = [weaken_assumption_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res7 = save_checked_variants(paper, idx, weaken_assumption_proofs,      0, "weaken_assumption", memory_file)
    # print("res7", res7)

    # quantifier_swap_proofs = [quantifier_swap_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res8 = save_checked_variants(paper, idx, quantifier_swap_proofs,        0, "quantifier_swap", memory_file)
    # print("res8", res8)

    # case_mismerge_proofs = [case_mismerge_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res9 = save_checked_variants(paper, idx, case_mismerge_proofs,          0, "case_mismerge", memory_file)
    # print("res9", res9)

    # circular_reasoning_proofs = [circular_reasoning_proof(proof, paper, idx, memory_file) for _ in range(nb_variants)]
    # res10 = save_checked_variants(paper, idx, circular_reasoning_proofs,    0, "circular_reasoning", memory_file)
    # print("res10", res10)
    # here add all the other modifications, correct and incorrect
    # if res0 + res1 + res2 + res3 + res4 + res5 + res6 + res7 + res8 + res9 + res10 == 11*nb_variants:
    #     print("perfect", idx)
    # else:
    #     print("not perfect", idx, res0, res1, res2, res3, res4, res5, res6, res7, res8, res9, res10)
    # do the same for the other modifications
if __name__ == "__main__":
    # Exemple d'article + énoncé
    paper = "2407.02412"
    # paper = "2407.10852"
    idx = 4
    memory_file = "memory.json"   
    generate_testcases(paper, idx, memory_file, nb_variants=1)
















































