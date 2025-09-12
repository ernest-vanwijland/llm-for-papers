from pipeline import *
from pipeline_util import *
from api import *
from verifier import *
import json
from prompts import verification_system_prompt, verification_reminder
import os
from generate_proofs_util import *

def generate_testcases(paper, idx, subfolder, nb_variants = 1):
    proof = get_proof(paper, idx)
    
    type_of_proof = "good" #get_proof_type(paper, idx, proof)
    if type_of_proof in ["figure_reference" or "external_reference"]:
        print(f"Proof {idx} of {paper} is not interesting.")
        return
    
    # correct proofs:
    save_testcase(paper, idx, 1, "original", proof, subfolder, f"{paper}_{idx}_original")
    
    paraphrases = [paraphrase_proof(proof, paper, idx) for _ in range(nb_variants)]
    for p in paraphrases:
        save_testcase(paper, idx, 1, "paraphrase", p, subfolder, f"{paper}_{idx}_paraphrase")
    
    rename_vars_proofs = [rename_vars_proof(proof, paper, idx) for _ in range(nb_variants)]
    for p in rename_vars_proofs:
        save_testcase(paper, idx, 1, "rename_vars", p, subfolder, f"{paper}_{idx}_rename")
    
    # incorrect proofs:
    drop_key_step_proofs = [drop_key_step_proof(proof, paper, idx) for _ in range(nb_variants)]
    for p in drop_key_step_proofs:
        save_testcase(paper, idx, 0, "drop_key_step", p, subfolder, f"{paper}_{idx}_drop")

    quantifier_swap_proofs = [quantifier_swap_proof(proof, paper, idx) for _ in range(nb_variants)]
    for p in quantifier_swap_proofs:
        save_testcase(paper, idx, 0, "quantifier_swap", p, subfolder, f"{paper}_{idx}_swap")
    
    case_mismerge_proofs = [case_mismerge_proof(proof, paper, idx) for _ in range(nb_variants)]
    for p in case_mismerge_proofs:
        save_testcase(paper, idx, 0, "case_mismerge", p, subfolder, f"{paper}_{idx}_mismerge")

if __name__ == "__main__":
    # Exemple d'article + énoncé
    paper = "2407.02412"
    # init_memory("2407.10852")
    # paper = "2407.10852"
    idx = 0
    generate_testcases(paper, idx, nb_variants=1)
















































