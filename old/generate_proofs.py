from pipeline import *
from pipeline_util import *
from api import *
from poubelle.checker import *
import json
from prompts import verification_system_prompt, verification_reminder
import os
from generate_proofs_util import *

def verify_given_solution(paper, idx, solution):
    statement = get_problem_statement(paper, idx)
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

ALLOWED_REASON_LABELS = [
    "valid",
    "drop_key_step",
    "wrong_bound",
    "weaken_assumption",
    "quantifier_swap",
    "case_mismerge",
    "circular_reasoning",
    "unknown"
]

def normalize_reason_llm(details: str, is_valid: int|None) -> str:
    fallback = "valid" if is_valid == 1 else "unknown"
    if not isinstance(details, str) or not details.strip():
        return fallback
    labels = ", ".join(ALLOWED_REASON_LABELS)
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
    return label if label in ALLOWED_REASON_LABELS else fallback

def check_testcase(paper, toprove, expected_validity, expected_reason, proof):
    """ function that checks that the testcase is correct """

    print("Checking testcase:", paper, toprove, expected_validity, expected_reason)
    detailed_verif, grade = verify_given_solution(paper, toprove, proof) #pas assez performant ?
    print("verify pass", grade)
    validity_ok = grade == expected_validity
    print("validity ok:", validity_ok)
    # 3) Trouver la raison
    found_reason = normalize_reason_llm(detailed_verif, grade)
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
        "details_verif": detailed_verif
    }

def save_checked_variants(paper, idx, variants, expected_validity, method_label):
    expected_reason = "valid" if expected_validity == 1 else method_label

    saved = 0
    for v in variants:
        
        res = check_testcase(paper, idx, expected_validity, expected_reason, v)
        if res["validity_ok"] and res["reason_ok"]:
            ok = save_testcase(paper, idx, expected_validity, method_label, v, f"{paper}_{idx}_{method_label}")
            if ok:
                saved += 1
        else:
            print(f"Skipped saving {method_label} due to failed check:", res)
        print(res)
    return saved

def define_proof_cat(paper, idx):
    proof, _ = get_proof(paper, idx)
    prompt=f"""
    ### Instructions ###
    You are given a mathematical proof from an academic paper. Your task is to classify the proof into exactly ONE of the following categories based on its dependencies and references.

    ### Categories ###
    1.  `self_contained`: The proof is entirely self-contained. All logic and justifications are present within the proof's text itself, without needing to refer to other parts of the paper or external documents.
    2.  `internal_reference`: The proof explicitly refers to other numbered or named parts of the same paper. Examples include citing a Lemma, Theorem, Corollary, Equation, or Section (e.g., "by Lemma 3.1", "from Equation (5)", "as defined in Section 2").
    3.  `figure_reference`: The proof's justification relies on a visual element like a figure, diagram, table, or schema within the paper (e.g., "as shown in Figure 2", "the construction in the diagram shows...").
    4.  `external_reference`: The proof cites an external work, such as another research paper, a book, or a technical report (e.g., "by the result in [15]", "as shown by Smith et al. [2021]").

    ### Task ###
    Analyze the provided proof and determine which category it best fits. Choose the most specific category that applies. If multiple types of references exist, prioritize them in this order: `external_reference`, `figure_reference`, `internal_reference`.

    Output ONLY the single category label (e.g., `self_contained`, `internal_reference`, `figure_reference`, `external_reference`) and nothing else.

    ### Proof ###
    {proof}
    """
    category = request([prompt], contents=[full(paper)])
    save_proof_support(paper, idx, category.strip())
    return category.strip()

def define_proof_cat_all(paper, max_proofs=100):
   
    results = []
    for idx in range(max_proofs):
        stmt = get_problem_statement(paper, idx)
        if not stmt or str(stmt).strip().upper() == "NONE":
            break
        cat = define_proof_cat(paper, idx)
        results.append({"idx": idx, "category": cat})
    return results

def generate_testcases(paper, idx, nb_variants=1):
    proof, is_new = get_proof(paper, idx)
    if is_new:
        save_testcase(paper, idx, 1, "original", proof, f"{paper}_{idx}_original")
    cat=define_proof_cat(paper, idx)
    print("Proof category:", cat)
    # ------- sanitary check -------
    res_sanitary = save_checked_variants(paper, idx, [proof],                   1, "sanitary_check")
    print("res_sanitary", res_sanitary)
    # ------- verification -------
    paraphrases = [paraphrase_proof(proof, paper, idx) for _ in range(nb_variants)]
    res0 = save_checked_variants(paper, idx, paraphrases,                   1, "paraphrase")
    print("res0", res0)

    # rename_vars_proofs = [rename_vars_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res1 = save_checked_variants(paper, idx, rename_vars_proofs,            1, "rename_vars")
    # print("res1", res1)

    # reorder_noncritical_proofs = [reorder_noncritical_proof(proof, paper, idx for _ in range(nb_variants)]
    # res2 = save_checked_variants(paper, idx, reorder_noncritical_proofs,    1, "reorder_noncritical")
    # print("res2", res2)

    # expand_justifications_proofs = [expand_justifications_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res3 = save_checked_variants(paper, idx, expand_justifications_proofs,  1, "expand_justifications")
    # print("res3", res3)

    # compress_justifications_proofs = [compress_justifications_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res4 = save_checked_variants(paper, idx, compress_justifications_proofs,1, "compress_justifications")
    # print("res4", res4)
    # ------- falsification --------
    drop_key_step_proofs = [drop_key_step_proof(proof, paper, idx) for _ in range(nb_variants)]
    res5 = save_checked_variants(paper, idx, drop_key_step_proofs, 0, "drop_key_step")
    print("res5", res5)

    # wrong_bound_proofs = [wrong_bound_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res6 = save_checked_variants(paper, idx, wrong_bound_proofs,            0, "wrong_bound")
    # print("res6", res6)

    # weaken_assumption_proofs = [weaken_assumption_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res7 = save_checked_variants(paper, idx, weaken_assumption_proofs,      0, "weaken_assumption")
    # print("res7", res7)

    # quantifier_swap_proofs = [quantifier_swap_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res8 = save_checked_variants(paper, idx, quantifier_swap_proofs,        0, "quantifier_swap")
    # print("res8", res8)

    # case_mismerge_proofs = [case_mismerge_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res9 = save_checked_variants(paper, idx, case_mismerge_proofs,          0, "case_mismerge")
    # print("res9", res9)

    # circular_reasoning_proofs = [circular_reasoning_proof(proof, paper, idx) for _ in range(nb_variants)]
    # res10 = save_checked_variants(paper, idx, circular_reasoning_proofs,    0, "circular_reasoning")
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
    # init_memory("2407.10852")
    # paper = "2407.10852"
    idx = 0
    generate_testcases(paper, idx, nb_variants=1)
















































