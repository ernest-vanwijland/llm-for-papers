from pipeline import *
from pipeline_util import *
from api import *
from checker import *
import json
import os

# ------------------
# Small utilities
# ------------------

testcase_counter = 0

def _now_iso():
    return __import__('datetime').datetime.now().isoformat()

def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

# ------------------
# Testcase I/O (kept, with tiny fixes)
# ------------------

def save_testcase(paper, toprove, validity, comment, proof, name=None):
    """Save one testcase JSON under test/"""
    global testcase_counter
    if name is None:
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
        "timestamp": _now_iso()
    }
    _ensure_dir(name)
    try:
        with open(name, 'w', encoding='utf-8') as f:
            json.dump(testcase, f, indent=2, ensure_ascii=False)
        print(f"Testcase saved to {name}")
        return True
    except Exception as e:
        print(f"Error saving testcase to {name}: {e}")
        return False

# ------------------
# Proof extraction (keep user's style: no LaTeX wrapper; use LaTeX for math)
# ------------------

def get_proof(paper, idx, memory_file):
    """
    Return the proof text as it appears in the paper (no wrapper),
    using LaTeX notation for mathematical symbols.
    """
    prompt = f"""
    ### Instructions ###

    You are given an academic paper and one of the statements that appears in the paper.
    Your job is to return the proof of the statement as it appears in the paper, and nothing else.
    You will use latex for mathematical notations.
    You should provide the whole proof and make sure it is exactly the same as the one that appears in the paper.
    Sometimes, the proof might not be right after the statement in the paper.

    ### Statement ###

    {get_problem_statement(paper, idx, memory_file)}
    """
    return request([prompt], contents=[full(paper)])

# ------------------
# Diversification primitives (one idea per function)
# ------------------

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
    return request([prompt], contents=[full(paper)])

def rename_vars_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Consistently rename variables and symbols throughout the proof (e.g., $x\\to u$, $S\\to T$) without changing the logic.
    Keep LaTeX consistent and compile-ready. Preserve correctness.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def reorder_noncritical_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Reorder independent steps or cases (e.g., prove Case 2 before Case 1) without changing dependencies or logic.
    Preserve correctness rigorously.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def expand_justifications_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Expand terse parts by inserting short rigorous justifications for steps that were implicit.
    Keep mathematics identical; only add necessary explanations.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def compress_justifications_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Compress the proof by removing redundant commentary while preserving all logically necessary steps.
    Keep mathematics identical.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

# --- invalidating edits ---

def drop_key_step_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Remove exactly one logically essential step so the proof contains a fatal gap but remains superficially plausible.
    Do NOT add new arguments that fix the gap.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def wrong_bound_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Introduce a subtle but fatal inequality/constant error (e.g., replace $\\le$ by $<$) so the proof becomes invalid.
    Keep the rest unchanged and plausible.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def weaken_assumption_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Remove or weaken a critical assumption before it is used so a lemma/theorem application becomes unjustified.
    The resulting proof must be invalid but look smooth.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def quantifier_swap_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Alter the order/scope of quantifiers in a key step (swap $\\forall$ / $\\exists$ improperly) to create a fatal logical flaw.
    Keep the rest intact.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def case_mismerge_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Mishandle or omit one necessary case in the case analysis so the conclusion is invalid.
    Keep the text plausible.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

def circular_reasoning_proof(proof, paper, idx, memory_file):
    prompt = f"""
    ### Instructions ###
    Introduce circular reasoning by using the statement (or equivalent) as justification for a step.
    Keep the text plausible; resulting proof must be invalid.
    Output ONLY the proof text, using latex for mathematical notations.

    ### Statement ###
    {get_problem_statement(paper, idx, memory_file)}

    ### Proof ###
    {proof}
    """
    return request([prompt], contents=[full(paper)])

# ------------------
# Grading (shared tiny helper, factored)
# ------------------

def grade_text_with_checker(paper, idx, text, memory_file, want_logs=False):
    """Inject text as solution, grade, then restore. Return (grade:int|None, logs:str|None)."""
    general = load_memory(memory_file) or {}
    prev = None
    try:
        if "solutions" in general and isinstance(general["solutions"], list) and len(general["solutions"]) > idx:
            prev = general["solutions"][idx]
        else:
            if "solutions" not in general or not isinstance(general.get("solutions"), list):
                general["solutions"] = []
        save_solution(idx, text, general)
        save_memory(memory_file, general)

        if want_logs:
            logs, g = verify_solution(paper, idx, memory_file)
            return int(g), logs
        else:
            g = grade_idx(paper, idx, general) if 'grade_idx' in globals() else None
            return int(g) if g is not None else None, None
    finally:
        general = load_memory(memory_file) or {}
        if "solutions" not in general or not isinstance(general.get("solutions"), list):
            general["solutions"] = []
        while len(general["solutions"]) <= idx:
            general["solutions"].append("")
        general["solutions"][idx] = prev if prev is not None else ""
        save_memory(memory_file, general)

# ------------------
# memoryProof.json (per-article store) — tiny, composable helpers
# ------------------

def load_extraction_memory(path):
    m = load_memory(path)
    return m if isinstance(m, dict) else {}

def ensure_article(mem, paper):
    mem.setdefault(paper, {})
    mem[paper].setdefault("proofs", {})
    return mem[paper]["proofs"]

def ensure_proof_record(mem, paper, idx):
    proofs = ensure_article(mem, paper)
    rec = proofs.setdefault(str(idx), {"original": {"text": None, "validity": None}, "variants": []})
    rec.setdefault("original", {"text": None, "validity": None})
    rec.setdefault("variants", [])
    return rec

def record_original(mem, paper, idx, text, validity=None):
    rec = ensure_proof_record(mem, paper, idx)
    rec["original"]["text"] = text
    rec["original"]["validity"] = validity

def append_variant(mem, paper, idx, variant):
    rec = ensure_proof_record(mem, paper, idx)
    rec["variants"].append(variant)

# ------------------
# Variants factory (mapping method -> function)
# ------------------

VALID_METHODS = [
    "paraphrase", "rename_vars", "reorder_noncritical",
    "expand_justifications", "compress_justifications"
]

INVALID_METHODS = [
    "drop_key_step", "wrong_bound", "weaken_assumption",
    "quantifier_swap", "case_mismerge", "circular_reasoning"
]

def expected_valid(method):
    return method in VALID_METHODS

def method_fn(method):
    return {
        "paraphrase": paraphrase_proof,
        "rename_vars": rename_vars_proof,
        "reorder_noncritical": reorder_noncritical_proof,
        "expand_justifications": expand_justifications_proof,
        "compress_justifications": compress_justifications_proof,
        "drop_key_step": drop_key_step_proof,
        "wrong_bound": wrong_bound_proof,
        "weaken_assumption": weaken_assumption_proof,
        "quantifier_swap": quantifier_swap_proof,
        "case_mismerge": case_mismerge_proof,
        "circular_reasoning": circular_reasoning_proof,
    }[method]

# ------------------
# JSON export per-article (dataset of variants)
# ------------------

def export_variants_json(paper, variants, out_path=None):
    path = out_path or f"data/{paper}/proof_variants.json"
    _ensure_dir(path)
    data = {"paper": paper, "variants": []}
    if os.path.exists(path):
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
        except Exception:
            data = {"paper": paper, "variants": []}
    if data.get("paper") != paper:
        data = {"paper": paper, "variants": []}
    data["variants"].extend(variants)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Variants saved to {path}")
    return path

# ------------------
# High-level generators (short, orchestrate tiny helpers)
# ------------------

def build_variants(proof, paper, idx, memory_file, methods=None, k_per_method=1):
    methods = methods or (VALID_METHODS + INVALID_METHODS)
    variants = []
    # statement fetched inside the primitive functions (keeps each function focused)
    for m in methods:
        fn = method_fn(m)
        for j in range(k_per_method):
            text = fn(proof, paper, idx, memory_file)
            variants.append({
                "proof_idx": idx,
                "variant_id": f"{idx}-{m}-{j}",
                "method": m,
                "text": text,
                "expected_valid": expected_valid(m),
                "graded_valid": None,
                "detailed_verif": None
            })
    return variants

def grade_variants_inplace(paper, idx, memory_file, variants, with_logs=False):
    for v in variants:
        g, log = grade_text_with_checker(paper, idx, v["text"], memory_file, want_logs=with_logs)
        v["graded_valid"] = g
        v["detailed_verif"] = log if with_logs else None

# ------------------
# Public pipeline (preserve user's generate_testcases, extend)
# ------------------

def check_testcase(paper, toprove, validity, comment, proof):
    """Minimal placeholder check; can be expanded to structural checks."""
    return isinstance(proof, str) and len(proof.strip()) > 0

def generate_testcases(paper, idx, memory_file,
                       extraction_file=None,
                       methods=None, k_per_method=1,
                       grade_original=False,
                       grade_variants=False,
                       export_json=True):
    """
    1) Extract base proof (original).
    2) Generate variants (valid + invalid).
    3) Optionally grade original and variants.
    4) Save per-testcase JSONs (kept).
    5) Optionally record into memoryProof.json (per-article, keyed by paper).
    6) Optionally export per-article dataset JSON.
    """
    proof = get_proof(paper, idx, memory_file)
    if grade_original and proof:
        g, _ = grade_text_with_checker(paper, idx, proof, memory_file, want_logs=False)
    else:
        g = None

    # Save original testcase
    save_testcase(paper, idx, 1, "original", proof, f"original_{paper}_{idx}")

    # Build variants
    variants = build_variants(proof, paper, idx, memory_file, methods, k_per_method)
    if grade_variants and variants:
        grade_variants_inplace(paper, idx, memory_file, variants, with_logs=False)

    # Save testcases for variants
    for v in variants:
        val = v["graded_valid"] if v["graded_valid"] is not None else (1 if v["expected_valid"] else 0)
        save_testcase(paper, idx, val, v["method"], v["text"], f"{v['method']}_{paper}_{idx}")

    # Update extraction memoryProof.json
    if extraction_file:
        mem = load_extraction_memory(extraction_file)
        record_original(mem, paper, idx, proof, g)
        for v in variants:
            append_variant(mem, paper, idx, {
                "variant_id": v["variant_id"],
                "method": v["method"],
                "text": v["text"],
                "expected_valid": v["expected_valid"],
                "graded_valid": v["graded_valid"],
                "detailed_verif": v["detailed_verif"]
            })
        save_memory(extraction_file, mem)

    # Export article-level dataset JSON
    if export_json:
        export_variants_json(paper, variants)

    return {"original": proof, "variants": variants}
