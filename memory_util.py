from api import *
from prompts import *
import json
import os

def full(paper):
    return f"data/{paper}/full.pdf"

def noproof(paper):
    return f"data/{paper}/noproof.pdf"

def init_memory(paper):
    memory_file = f"memory/memory_{paper}.json"
    os.makedirs("memory", exist_ok=True)
    if not os.path.exists(memory_file):
        memory = {
            "nbtoprove": -1,
            "statements": [],
            "proofs": [],
            "solutions": [],
            "verifs": [],
            "grades": [],
            "proof_type": [],
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)

def load_memory(paper):
    memory_file = f"memory/memory_{paper}.json"
    if not os.path.exists(memory_file):           
        init_memory(paper)
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory = json.load(f)
        #print(f"Memory loaded from {memory_file}")
        return memory
    except Exception as e:
        #print(f"Error loading memory from {memory_file}: {e}")
        return None

def save_memory(paper, memory):
    memory_file = f"memory/memory_{paper}.json"
    memory["timestamp"] = __import__('datetime').datetime.now().isoformat()
    try:
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
        #print(f"Memory saved to {memory_file}")
        return True
    except Exception as e:
        #print(f"Error saving memory to {memory_file}: {e}")
        return False

def get_solution(paper, idx):
    memory = load_memory(paper)
    if len(memory["solutions"]) <= idx:
        return None
    return memory["solutions"][idx]

def save_solution(paper, idx, solution):
    memory = load_memory(paper)
    while len(memory["solutions"]) <= idx:
        memory["solutions"].append("")
    memory["solutions"][idx] = solution
    save_memory(paper, memory)

def save_proof(paper, idx, proof):
    memory = load_memory(paper)
    while len(memory["proofs"]) <= idx:
        memory["proofs"].append(None)
    memory["proofs"][idx] = proof
    save_memory(paper, memory)

def get_proof(paper, idx):
    memory = load_memory(paper)
    if len(memory["proofs"]) > idx and memory["proofs"][idx] != None:
        return memory["proofs"][idx]
    
    statement = get_problem_statement(paper, idx)
    if statement == None:
        return None
    
    prompt = f"""
    ### Instructions ###
    
    You are given an academic paper and one of the statements that appears in the paper. Your job is to return the proof of the statement as it appears in the paper, and nothing else. You will use latex for mathematical notations. You should provide the whole proof and make sure it is exactly the same as the one that appears in the paper. Sometimes, the proof might not be right after the statement in the paper.
    
    ### Statement ###
    
    {statement}
    """
    proof = request(prompt, files = [full(paper)])
    save_proof(paper, idx, proof)
    return proof

def save_verif(paper, idx, verif):
    memory = load_memory(paper)
    while len(memory["verifs"]) <= idx:
        memory["verifs"].append("")
    memory["verifs"][idx] = verif
    save_memory(paper, memory)

def save_grade(paper, idx, grade):
    memory = load_memory(paper)
    while len(memory["grades"]) <= idx:
        memory["grades"].append(-1)
    memory["grades"][idx] = grade
    save_memory(paper, memory)

def get_verif(paper, idx):
    memory = load_memory(paper)
    if len(memory["verifs"]) <= idx:
        return None
    return memory["verifs"][idx]

def save_proof_type(paper, idx, proof_type):
    memory = load_memory(paper)
    while len(memory["proof_type"]) <= idx:
        memory["proof_type"].append("")
    memory["proof_type"][idx] = proof_type
    save_memory(paper, memory)

def get_proof_type(paper, idx):
    memory = load_memory(paper)
    if len(memory["proof_type"]) <= idx:
        return None
    return memory["proof_type"][idx]

def save_toprove(paper, x):
    memory = load_memory(paper)
    memory["nbtoprove"] = x
    while len(memory["statements"]) < x:
        memory["statements"].append(None)
    save_memory(paper, memory)

def get_toprove(paper):
    memory = load_memory(paper)
    x = memory["nbtoprove"]
    if x == -1:
        x = int(request(number_of_toprove_prompt, files = [noproof(paper)]))
        save_toprove(paper, x)
    return x

def get_problem_statement(paper, idx):
    memory = load_memory(paper)
    if len(memory["statements"]) <= idx or memory["statements"][idx] == None:
        while len(memory["statements"]) <= idx:
            memory["statements"].append(None)
        statement = request(problem_statement_prompt + str(idx), files = [noproof(paper)])
        if statement == "NONE":
            return None
        memory["statements"][idx] = statement
        save_memory(paper, memory)
    return memory["statements"][idx]















































