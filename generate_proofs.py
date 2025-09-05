from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from textwrap import dedent
import json
import os

from pipeline import *
from pipeline_util import *
from api import *
from checker import *

# =============================
# Extraction-memory (memoryProof.json) helpers
# Schema (top-level keyed by paper):
# {
#   "<paper>": {
#       "proofs": {
#           "<idx>": {
#               "original": {
#                   "text": "<extracted proof text without LaTeX wrapper>",
#                   "validity": null | 0 | 1   # BEFORE any alteration (optional grading)
#               },
#               "variants": [
#                   {
#                       "variant_id": "idx-mode-j",
#                       "method": "<mode>",
#                       "text": "<variant proof text>",
#                       "expected_valid": true/false,
#                       "graded_valid": null | 0 | 1,  # AFTER alteration (if graded)
#                       "detailed_verif": "..."        # optional
#                   }
#               ]
#           }
#       }
#   },
#   ...
# }
# =============================

def _load_or_init_extraction_memory(extraction_file: str) -> Dict[str, Any]:
    mem = load_memory(extraction_file)
    if mem is None or not isinstance(mem, dict):
        mem = {}
        save_memory(extraction_file, mem)
    return mem

def _ensure_article_bucket(mem: Dict[str, Any], paper: str) -> None:
    if paper not in mem or not isinstance(mem.get(paper), dict):
        mem[paper] = {}
    if "proofs" not in mem[paper] or not isinstance(mem[paper].get("proofs"), dict):
        mem[paper]["proofs"] = {}

def _ensure_proof_record(mem: Dict[str, Any], paper: str, idx: int) -> Dict[str, Any]:
    _ensure_article_bucket(mem, paper)
    proofs = mem[paper]["proofs"]
    key = str(idx)
    if key not in proofs or not isinstance(proofs.get(key), dict):
        proofs[key] = {"original": {"text": None, "validity": None}, "variants": []}
    else:
        if "original" not in proofs[key]:
            proofs[key]["original"] = {"text": None, "validity": None}
        if "variants" not in proofs[key]:
            proofs[key]["variants"] = []
    return proofs[key]

def _record_original(mem: Dict[str, Any], paper: str, idx: int, text: str, validity: Optional[int]) -> None:
    rec = _ensure_proof_record(mem, paper, idx)
    rec["original"]["text"] = text
    rec["original"]["validity"] = validity

def _append_variant(mem: Dict[str, Any], paper: str, idx: int, variant: Dict[str, Any]) -> None:
    rec = _ensure_proof_record(mem, paper, idx)
    rec["variants"].append(variant)

# =============================
# Proof extraction (no LaTeX wrapper enforced)
# =============================

def get_proof(
    paper: str,
    idx: int,
    memory_file: str,
    extraction_file: str,
    verifyTwice: bool = False,
    grade_original_with_checker: bool = False
) -> Optional[str]:
    """
    Extract the proof text (without forcing LaTeX \\begin{proof} wrapper) for TOPROVE idx.
    Anchors on the statement recovered by get_problem_statement(paper, idx, memory_file).
    Caches into extraction memory under: mem[paper]['proofs'][idx]['original'].
    If grade_original_with_checker=True, we compute 'validity' BEFORE alteration using the checker.
    """
    mem = _load_or_init_extraction_memory(extraction_file)
    rec = _ensure_proof_record(mem, paper, idx)

    # Already cached?
    cached = rec["original"]["text"]
    if cached:
        return cached

    # Anchor on the statement
    statement = get_problem_statement(paper, idx, memory_file)
    if not statement or statement == "NONE":
        return None

    # Primary prompt: output ONLY the proof (no wrapper), but keep LaTeX notation for math
    prompt = f"""
    You are given:
    1) The full PDF of a paper (with proofs).
    2) The statement below which appears in the paper and is immediately followed by its proof.

    --- STATEMENT ---
    {statement}
    --- END STATEMENT ---

    Task:
    • Find this statement in the paper.
    • Extract the exact proof that proves this statement, starting immediately after the statement and ending at the end of the proof (i.e., up to and including a QED marker or the start of a new section).
    • Output ONLY the proof text (no \\begin{{proof}} wrapper). Use LaTeX notation for mathematical characters when needed.
    """
    proof = request([prompt], contents=[full(paper)])

    if verifyTwice:
        fallback_prompt = (
            f"Your job is to extract the proof of the statement replaced by TOPROVE {idx} from the attached paper. "
            "The proof might be a single paragraph or span multiple pages. "
            "Extract the entire proof and nothing else. "
            "The proof starts right after the statement it proves, and ends with a QED marker or the start of a new section. "
            "Output ONLY the proof text (no LaTeX proof environment)."
        )
        proof2 = request([fallback_prompt], contents=[full(paper), noproof(paper)])
        if isinstance(proof, str) and isinstance(proof2, str) and proof.strip() == proof2.strip():
            proof = proof2
        else:
            print(f"[Warn] Discrepancy in proof extraction for {paper} TOPROVE {idx}.")

    validity_before = None
    if proof and grade_original_with_checker:
        # Temporarily inject proof into the general memory to reuse checker.verify_solution,
        # then revert previous memory["solutions"][idx].
        general = load_memory(memory_file) or {}
        prev_solution = None
        try:
            # snapshot previous
            if isinstance(general, dict):
                if "solutions" in general and isinstance(general["solutions"], list) and len(general["solutions"]) > idx:
                    prev_solution = general["solutions"][idx]
                else:
                    # ensure list long enough
                    if "solutions" not in general or not isinstance(general.get("solutions"), list):
                        general["solutions"] = []
                save_solution(idx, proof, general)
                save_memory(memory_file, general)

            # run checker (returns grade 0/1)
            grade_value = grade_idx(paper, idx, general) if 'grade_idx' in globals() else verify_solution(paper, idx, memory_file)
            if isinstance(grade_value, tuple):
                # if verify_solution returned (detailed, grade) in some implementations
                _, gv = grade_value
                validity_before = int(gv)
            elif isinstance(grade_value, (int, bool)):
                validity_before = int(grade_value)
            else:
                try:
                    validity_before = int(grade_value)  # best effort
                except Exception:
                    validity_before = None
        finally:
            # restore previous solution in general memory
            general = load_memory(memory_file) or {}
            if "solutions" not in general or not isinstance(general.get("solutions"), list):
                general["solutions"] = []
            while len(general["solutions"]) <= idx:
                general["solutions"].append("")
            general["solutions"][idx] = prev_solution if prev_solution is not None else ""
            save_memory(memory_file, general)

    # Cache and return
    if proof:
        _record_original(mem, paper, idx, proof, validity_before)
        save_memory(extraction_file, mem)
        return proof
    return None

# =============================
# Diversification
# =============================

# Methods that SHOULD preserve validity (expected_valid = True)
VALID_PRESERVING_METHODS = [
    "paraphrase",              # rephrase sentences, keep math identical
    "rename_vars",             # consistent alpha-renaming of variables/symbols
    "reorder_noncritical",     # reorder independent steps/cases
    "expand_justifications",   # make implicit steps explicit
    "compress_justifications", # remove redundant verbosity, keep logic
]

# Methods designed to likely BREAK validity (expected_valid = False)
INVALIDATING_METHODS = [
    "drop_key_step",        # remove a logically essential step
    "wrong_bound",          # alter <= / < or constants in inequalities
    "weaken_assumption",    # remove a critical hypothesis before using a lemma
    "quantifier_swap",      # swap ∀/∃ order or scope improperly
    "case_mismerge",        # incorrectly conclude from partial case analysis
    "circular_reasoning",   # explicitly use the statement being proved
]

def _variant_prompt(statement: str, base_proof: str, mode: str) -> Tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for a given diversification mode.
    The model must output ONLY the proof text (no LaTeX environment), but may use LaTeX notation for math.
    """
    sys = "You are a careful proof editor. Follow the instructions precisely. Use LaTeX notation for mathematical characters when needed. Output only the proof text."
    header = f"--- STATEMENT ---\n{statement}\n--- END STATEMENT ---\n\n--- BASE PROOF ---\n{base_proof}\n--- END BASE PROOF ---\n\n"
    if mode == "paraphrase":
        user = header + dedent(r"""
        Task: Rewrite the BASE PROOF as a paraphrase in natural language while keeping every mathematical step and justification logically identical.
        Constraints:
        - Preserve correctness rigorously.
        - DO NOT change any mathematical content.
        - Keep the same structure of claims and equations, but you may rephrase sentences.
        Output ONLY the proof text.
        """)
    elif mode == "rename_vars":
        user = header + dedent(r"""
        Task: Consistently rename variables and symbols throughout the BASE PROOF (e.g., replace $x$ by $u$, $S$ by $T$), without changing the logic.
        Constraints:
        - Preserve correctness rigorously.
        Output ONLY the proof text.
        """)
    elif mode == "reorder_noncritical":
        user = header + dedent(r"""
        Task: Reorder independent steps or cases in the BASE PROOF (e.g., prove Case 2 before Case 1) without changing the logical content.
        Constraints:
        - Do NOT alter any dependencies. Do not move a step before a prerequisite.
        - Preserve correctness rigorously.
        Output ONLY the proof text.
        """)
    elif mode == "expand_justifications":
        user = header + dedent(r"""
        Task: Expand terse parts of the BASE PROOF by inserting short, rigorous justifications for steps that were previously implicit.
        Constraints:
        - Preserve correctness rigorously.
        - Keep mathematics identical; only add missing explanations.
        Output ONLY the proof text.
        """)
    elif mode == "compress_justifications":
        user = header + dedent(r"""
        Task: Compress the BASE PROOF by removing redundant commentary while preserving all logically necessary steps.
        Constraints:
        - Preserve correctness rigorously.
        - Keep mathematics identical.
        Output ONLY the proof text.
        """)
    elif mode == "drop_key_step":
        user = header + dedent(r"""
        Task: Modify the BASE PROOF by removing exactly one logically essential step so that the proof now contains a fatal gap (but still looks superficially plausible).
        Constraints:
        - Produce a proof-like text that appears smooth but is INVALID due to the removed step.
        - Do NOT add new correct arguments that close the gap.
        Output ONLY the proof text.
        """)
    elif mode == "wrong_bound":
        user = header + dedent(r"""
        Task: Introduce a subtle but fatal inequality error in the BASE PROOF (e.g., replace $\le$ by $<$ or modify a constant) so that the proof becomes INVALID.
        Constraints:
        - Keep the rest unchanged and plausible.
        - Ensure the resulting proof is incorrect.
        Output ONLY the proof text.
        """)
    elif mode == "weaken_assumption":
        user = header + dedent(r"""
        Task: Remove or weaken a critical assumption right before it is used so that the application of a lemma/theorem becomes unjustified, rendering the proof INVALID.
        Constraints:
        - Keep the narrative smooth.
        - Ensure the resulting proof is incorrect.
        Output ONLY the proof text.
        """)
    elif mode == "quantifier_swap":
        user = header + dedent(r"""
        Task: Alter the order/scope of quantifiers in a key step (swap $\forall$ and $\exists$ improperly), creating a subtle but fatal logical flaw.
        Constraints:
        - Keep the rest of the proof as intact as possible.
        - Ensure the resulting proof is incorrect.
        Output ONLY the proof text.
        """)
    elif mode == "case_mismerge":
        user = header + dedent(r"""
        Task: Modify the case analysis so that one necessary case is mishandled or omitted, causing an invalid conclusion.
        Constraints:
        - Keep the text plausible.
        - Ensure the resulting proof is incorrect.
        Output ONLY the proof text.
        """)
    elif mode == "circular_reasoning":
        user = header + dedent(r"""
        Task: Sneak in the statement being proved (or an equivalent) as justification for a step, creating circular reasoning that invalidates the proof.
        Constraints:
        - Keep the text plausible.
        - Ensure the resulting proof is incorrect.
        Output ONLY the proof text.
        """)
    else:
        user = header + "Rewrite the proof with light paraphrasing. Output ONLY the proof text."
    return sys, user

def create_variant(statement: str, base_proof: str, mode: str) -> str:
    sys, user = _variant_prompt(statement, base_proof, mode)
    return request([user], system_prompt=sys, contents=[])

def diversify_proof(
    paper: str,
    idx: int,
    memory_file: str,
    extraction_file: str,
    methods: Optional[List[str]] = None,
    k_per_method: int = 2,
    grade_with_checker: bool = False,
    out_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate diversified proof variants for (paper, idx).
    - Writes/extends a per-article JSON dataset at data/{paper}/proof_variants.json (unless out_path specified).
    - Also records variants into extraction memory under mem[paper]['proofs'][idx]['variants'] with 'graded_valid' (AFTER alteration).
    Returns the JSON record dictionary.
    Fields per variant in JSON: { 'proof_idx', 'variant_id', 'method', 'text', 'expected_valid', 'graded_valid', 'detailed_verif' }
    """
    if methods is None:
        methods = VALID_PRESERVING_METHODS + INVALIDATING_METHODS

    # Ensure the base proof exists (and record original with before-validity if requested)
    base_proof = get_proof(
        paper, idx, memory_file, extraction_file,
        verifyTwice=False, grade_original_with_checker=grade_with_checker
    )
    if not base_proof:
        raise ValueError(f"Could not extract base proof for TOPROVE {idx} in paper {paper}.")

    # Fetch statement
    statement = get_problem_statement(paper, idx, memory_file)
    if not statement or statement == "NONE":
        raise ValueError(f"No statement found for TOPROVE {idx} in paper {paper}.")

    expected_valid_map = {m: True for m in VALID_PRESERVING_METHODS}
    expected_valid_map.update({m: False for m in INVALIDATING_METHODS})

    mem = _load_or_init_extraction_memory(extraction_file)

    variants: List[Dict[str, Any]] = []
    for mode in methods:
        for j in range(k_per_method):
            text = create_variant(statement, base_proof, mode)
            graded_valid = None
            detailed_verif = None
            if grade_with_checker and text:
                # Temporarily grade via checker: inject into general memory, revert after.
                general = load_memory(memory_file) or {}
                prev_solution = None
                try:
                    if "solutions" in general and isinstance(general["solutions"], list) and len(general["solutions"]) > idx:
                        prev_solution = general["solutions"][idx]
                    else:
                        if "solutions" not in general or not isinstance(general.get("solutions"), list):
                            general["solutions"] = []
                    save_solution(idx, text, general)
                    save_memory(memory_file, general)

                    grade_value = grade_idx(paper, idx, general) if 'grade_idx' in globals() else verify_solution(paper, idx, memory_file)
                    if isinstance(grade_value, tuple):
                        _, gv = grade_value
                        graded_valid = int(gv)
                    elif isinstance(grade_value, (int, bool)):
                        graded_valid = int(grade_value)
                    else:
                        try:
                            graded_valid = int(grade_value)
                        except Exception:
                            graded_valid = None
                    detailed_verif = None  # can be filled if verify_solution returns logs in your setup
                finally:
                    # restore general memory
                    general = load_memory(memory_file) or {}
                    if "solutions" not in general or not isinstance(general.get("solutions"), list):
                        general["solutions"] = []
                    while len(general["solutions"]) <= idx:
                        general["solutions"].append("")
                    general["solutions"][idx] = prev_solution if prev_solution is not None else ""
                    save_memory(memory_file, general)

            variant_record = {
                "proof_idx": idx,
                "variant_id": f"{idx}-{mode}-{j}",
                "method": mode,
                "text": text,
                "expected_valid": bool(expected_valid_map.get(mode, True)),
                "graded_valid": graded_valid,
                "detailed_verif": detailed_verif
            }
            variants.append(variant_record)
            # Mirror into extraction memory under the article
            _append_variant(mem, paper, idx, {
                k: variant_record[k] for k in ["variant_id","method","text","expected_valid","graded_valid","detailed_verif"]
            })

    # Persist extraction memory
    save_memory(extraction_file, mem)

    # Also export per-article dataset JSON
    if out_path is None:
        out_path = f"data/{paper}/proof_variants.json"

    # Load & extend
    existing: Dict[str, Any] = {}
    try:
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
    except Exception:
        existing = {}

    if not existing or existing.get("paper") != paper:
        existing = {"paper": paper, "variants": []}
    existing["variants"].extend(variants)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return existing

# CLI for quick runs
if __name__ == "__main__":
    memory_file = "memory.json"         # general pipeline memory (statements/solutions/etc.)
    extraction_file = "memoryProof.json" # extraction memory (keyed by article)
    paper = "2407.02412"
    idx = 0

    # Extract and cache the base proof anchored by the statement
    proof = get_proof(paper, idx, memory_file, extraction_file, grade_original_with_checker=True)
    print("Base proof extracted:", bool(proof))

    # Generate variants (without grading by default to save tokens)
    result = diversify_proof(paper, idx, memory_file, extraction_file,methods=["paraphrase","simplify"] ,k_per_method=1, grade_with_checker=False)
    print(f"Wrote {len(result.get('variants', []))} variants to data/{paper}/proof_variants.json")
