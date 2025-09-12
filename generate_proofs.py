from pipeline import *
from pipeline_util import *
from api import *
from verifier import *
import json
from prompts import verification_system_prompt, verification_reminder
import os
from generate_proofs_util import *
import concurrent.futures

def generate_testcases(paper, idx, subfolder, nb_variants = 1):
    proof = get_proof(paper, idx)
    
    type_of_proof = "good" #get_proof_type(paper, idx, proof)
    if type_of_proof in ["figure_reference" or "external_reference"]:
        print(f"Proof {idx} of {paper} is not interesting.")
        return
    
    # correct proofs:
    save_testcase(paper, idx, 1, "original", proof, subfolder, f"{paper}_{idx}_original")
    print("Generating paraphrases...")
    # t = paraphrase_proof(proof, paper, idx)
    paraphrases = [paraphrase_proof(proof, paper, idx) for _ in range(nb_variants)]
    print(paraphrases)
    for p in paraphrases:
        save_testcase(paper, idx, 1, "paraphrase", p, subfolder, f"{paper}_{idx}_paraphrase")
    
    # switches = [switch_noncritical_proof(proof, paper, idx) for _ in range(nb_variants)]
    # for s in switches:
    #     save_testcase(paper, idx, 1, "switch", s, subfolder, f"{paper}_{idx}_switch")
    # # incorrect proofs:
    # hallucination_proofs = [hallucination_proof(proof, paper, idx) for _ in range(nb_variants)]
    # for h in hallucination_proofs:
    #     save_testcase(paper, idx, 0, "hallucination", h, subfolder, f"{paper}_{idx}_hallucination")

    # incomplete_proofs = [suppress_critical_paragraph_proof(proof, paper, idx) for _ in range(nb_variants)]
    # for inc in incomplete_proofs:
    #     save_testcase(paper, idx, 0, "incomplete", inc, subfolder, f"{paper}_{idx}_incomplete")
    
    # error_proofs = [add_error_step_proof(proof, paper, idx) for _ in range(nb_variants)]
    # for err in error_proofs:
    #     save_testcase(paper, idx, 0, "error", err, subfolder, f"{paper}_{idx}_error")

def generates_testcase_parralel(paper, idx, subfolder, nb_variants=2):
    proof = get_proof(paper, idx)
    
    type_of_proof = "good" #get_proof_type(paper, idx, proof)
    if type_of_proof in ["figure_reference" or "external_reference"]:
        print(f"Proof {idx} of {paper} is not interesting.")
        return
    
    # correct proofs:
    save_testcase(paper, idx, 1, "original", proof, subfolder, f"{paper}_{idx}_original")

    transformations = [
        # (paraphrase_proof, 1, "paraphrase"),
        # (switch_noncritical_proof, 1, "switch"),
        # (hallucination_proof, 0, "hallucination"),
        (suppress_critical_paragraph_proof, 0, "incomplete"),
        # (add_error_step_proof, 0, "error"),
    ]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for gen_func, correctness, label in transformations:
            for i in range(nb_variants):
                future = executor.submit(gen_func, proof, paper, idx)
                futures.append((future, correctness, label, i + 1))

        for future, correctness, label, variant_idx in futures:
            try:
                generated_proof = future.result()
                filename = f"{paper}_{idx}_{label}_{variant_idx}"
                save_testcase(paper, idx, correctness, label, generated_proof, subfolder, filename)
            except Exception as e:
                print(f"Error generating proof for {label}: {e}")


def print_proofs_from_folder(subfolder):
    """
    Prints all proofs from a given subfolder in the 'test' directory.
    """
    test_dir = os.path.join('test', subfolder)
    if not os.path.exists(test_dir):
        print(f"Directory not found: {test_dir}")
        return

    print(f"--- Proofs from {test_dir} ---")
    for filename in os.listdir(test_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(test_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    proof = data.get('proof', 'Proof not found in file.')
                    print(f"\n--- File: {filename} ---")
                    comment = data.get('comment', 'No comment found.')

                    print(f"----------- Comment -----------: {comment}")
                    print(proof)
            except json.JSONDecodeError:
                print(f"\n--- File: {filename} ---")
                print("Error: Could not decode JSON.")
            except Exception as e:
                print(f"\n--- File: {filename} ---")
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Exemple d'article + énoncé
    paper = "2502.08328"
    # init_memory("2407.10852")
    # paper = "2407.10852"
    idx = 35
    
    generates_testcase_parralel(paper, idx, "testing_validity2", nb_variants=3)
    # generate_testcases(paper, idx, "testing_validity2", nb_variants=2)
    print_proofs_from_folder("testing_validity2")















































