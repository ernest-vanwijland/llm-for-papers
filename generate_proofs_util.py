from pipeline import *
from pipeline_util import *
from api import *
from verifier import *
import json
from prompts import verification_system_prompt, verification_reminder
import os

testcase_counter = 0
def save_testcase(paper, toprove, validity, comment, proof, subfolder, name = None):
    global testcase_counter
    if name == None:
        name = f"test/{subfolder}/testcase_{testcase_counter}.json"
    else:
        name = f"test/{subfolder}/{name}_{testcase_counter}.json"
    if proof == None:
        print(f"Empty proof for {name}.")
        return
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

def get_proof_type(paper, idx, proof):
    prompt=f"""
    ### Instructions ###
    You are given a mathematical proof from an academic paper. Your task is to classify the proof into exactly ONE of the following categories based on its dependencies and references.

    ### Categories ###
    1.  `self_contained`: The proof is entirely self-contained. All logic and justifications are present within the proof's text itself, without needing to refer to other parts of the paper or external documents.
    2.  `internal_reference`: The proof explicitly refers to other numbered or named parts of the same paper. Examples include citing a Lemma, Theorem, Corollary, Equation, or Section (e.g., "by Lemma 3.1", "from Equation (5)", "as defined in Section 2").
    3.  `figure_reference`: The proof's justification relies on a visual element like a figure, diagram, table, or schema within the paper (e.g., "as shown in Figure 2", "the construction in the diagram shows...").
    4.  `external_reference`: The proof cites an external work, such as another research paper, a book, or a technical report (e.g., "by the result in [15]", "as shown by Smith et al. [2021]").

    ### Task ###
    Analyze the provided proof and determine which category it best fits. Choose the most specific category that applies. If multiple types of references exist, prioritize them in this order: `external_reference`, `figure_reference`, `internal_reference`, `self_contained`.

    Output ONLY the single category label (e.g., `self_contained`, `internal_reference`, `figure_reference`, `external_reference`) and nothing else.

    ### Proof ###
    {proof}
    """
    type_of_proof = request([prompt], contents=[full(paper)]).strip()
    save_proof_type(paper, idx, type_of_proof)
    return type_of_proof
# --------------------------------------------------------------
def paraphrase_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given a statement from a mathematics paper and the proof of the statement extracted from the paper.
    Your job is to rewrite the proof as a paraphrase in natural language while keeping every mathematical step and justification logically identical.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - DO NOT change the ordering of logically dependent steps.
        - DO NOT add or remove any steps.
        - Keep the same structure of claims and equations, but you may rephrase sentences.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [])

def switch_noncritical_proof(proof, paper, idx):
    prompt = f"""
### Instructions ###
You are given a statement from a mathematics paper, and its proof extracted from the paper.
Your task is to REORDER **at least one** pair of **independent** units in the proof so that the order of the output differs from the input, while preserving all dependencies and mathematical content.

**Movable units (examples):**
- Whole case blocks (“Case 1/2/...”) that do not depend on each other;
- Symmetric subarguments on disjoint sets or by symmetry A/B;
- Independent lemmas/claims proved in parallel and used only later jointly;
- Standalone reminders/definitions not used by each other.

**Rules:**
1) **Dependency safety:** Never move a unit before anything it depends on (uses a result/equation/assumption/definition introduced earlier).
2) **Minimal change:** Perform exactly one small permutation (swap two units or reorder a short list). If no block-level swap exists, **fallback**: swap two adjacent independent sentences (e.g., two parallel checks). The output MUST differ.
3) **No edits:** Keep all text and equations verbatim; only move units. Do not paraphrase, add, or delete content.
4) **Labels:** If needed, adjust only superficial labels (“Case 1/Case 2”) to remain consistent; do not change references or mathematics.

Output ONLY the proof text, using LaTeX for mathematical notations.

### Statement ###
{get_problem_statement(paper, idx)}

### Proof ###
{proof}
"""
    return request([prompt], contents = [])

def rename_vars_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given an academic paper, a statement in the paper and the proof of the statement extracted from the paper.
    Your job is to consistently rename variables and symbols throughout the proof (e.g., $x \\to u$, $S \\to T$) without changing the logic.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - DO NOT change the ordering of logically dependent steps.
        - DO NOT add or remove any steps.
        - Keep LaTeX notation consistent across the proof.
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
        - DO NOT change the ordering of logically dependent steps.
        - DO NOT add or remove any steps.
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
        - DO NOT change the ordering of logically dependent steps.
        - DO NOT add or remove any necessary steps.
        - DO NOT change any mathematical content.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [full(paper)])

# --- invalidating edits ---
def hallucination_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given a statement from an academic the paper and the proof of the statement extracted from the paper.
    Your job is to introduce a subtle but fatal hallucinated step that appears plausible but is logically unfounded or incorrect. Make sure your hallucination is a false mathematical truth presented as true, it needs to be a clearly unjustified statement within the proof.
        Constraints:
        - Keep the rest of the proof intact and plausible.
        - Ensure the resulting proof is invalid.
        - Make only a minimal change that causes the flaw.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [])

def suppress_critical_paragraph_proof(proof, paper, idx):

    prompt = f"""
### Instructions ###
You are given a statement from an academic paper, and its proof extracted from the paper.
Your task is to DELETE exactly one **consecutive** block so that the remaining proof looks superficially plausible but is **logically invalid** (a fatal, unrecoverable gap).

**Selection criteria (all required):**
1) **Critical bridge:** The block you delete is strictly necessary for a later step (e.g., a key bound, lemma application, existence/expansion/coupling, or counting/union-bound argument).
2) **Dependency break:** After deletion, at least one later sentence still relies on the deleted conclusion, making the proof invalid.
3) **Non-recoverability:** The missing content cannot be reconstructed from earlier definitions or trivial algebra elsewhere in the paper.
4) **Size:** Remove ≥ 2 sentences, OR at least one displayed equation **plus** its immediate textual justification.

**Do NOT:**
- Do not add, edit, paraphrase, or reorder any remaining text.
- Do not add placeholders or comments.
- Do not fix references/labels; keep the rest verbatim so the reliance remains visible.

**Coherence requirement:**
Keep the proof flowing and natural despite the deletion; the remaining text should still read smoothly, while the conclusion is no longer logically supported.

Output ONLY the proof text, using LaTeX for mathematical notations.

### Statement ###
{get_problem_statement(paper, idx)}

### Proof ###
{proof}
"""

    return request([prompt], contents = [])

def add_error_step_proof(proof, paper, idx):
    prompt = f"""
    ### Instructions ###
    You are given a statement from an academic paper and the proof of the statement extracted from the paper.
    Your job is to insert a fatal error step that appears plausible but is logically incorrect or unjustified.
        Constraints:
        - Keep the rest of the proof intact and plausible.
        - Ensure the resulting proof is invalid.
        - Make only the change that causes the flaw.
        Output ONLY the proof text, using latex for mathematical notations.
    
    ### Statement ###
    
    {get_problem_statement(paper, idx)}
    
    ### Proof ###
    
    {proof}
    """
    return request([prompt], contents = [])
# ---  ---
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



















































