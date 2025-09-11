from api import *
from memory_util import *
from generate_proofs import *
from checker import *
from prompts_checker import *
from test import *
import os
import glob


if __name__ == "__main__":
    API_KEYS_SET_USED = API_KEY_SET_ALL
    API_KEYS_USED = API_KEYS_SET_USED[2]

    print(API_KEYS_SET_USED, API_KEYS_USED)
    #prepare_testcases(one_proof, "one_proof", 0)
    # results = run_checker("one_proof", checker)
    #save_results(results, "results_one_proof.json")
    
   
    # results1 = run_checker_on_specific(dossier, checker_use, paper_id=paper_to_check, proof_indices=proofs_to_check)
    # save_results(results1, f"article_{paper_to_check}_results_lv1_checker_{'_'.join(map(str, proofs_to_check))}.json")
    checker_use = checker_lv2
    # checker_use = checker_lv2
    dossier = "ten_proofs"
    checker_name = checker_use.__name__

    # Définir les tâches à exécuter
    papers_and_proofs = {
        "2502.08328": [31, 32, 33, 34, 35],
        "2502.09440": [1, 2, 3, 4, 5]
    }



    print("\n--- SETUP FOR PARALLEL EXECUTION ---")
    tasks = []
    for paper, proofs in papers_and_proofs.items():
        for proof_idx in proofs:
            tasks.append((paper, proof_idx, checker_use, dossier))
    
    num_processes = min(len(tasks), os.cpu_count() or 1)
    print(f"Starting parallel processing with {num_processes} processes...")
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(run_and_save_task, tasks)
    print("All parallel tasks completed.")















































