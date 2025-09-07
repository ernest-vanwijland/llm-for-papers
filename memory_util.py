from api import *
from prompts import *
import json
import os

def full(paper):
    return f"data/{paper}/paper.pdf"

def noproof(paper):
    return f"data/{paper}/noproof/paper.pdf"

def init_memory(paper):
    memory_file = f"memory/memory_{paper}.json"
    os.makedirs("memory", exist_ok=True)
    if not os.path.exists(memory_file):
        # os.mknod(memory_file)
        memory = {
            "statements": [],
            "solutions": [],
            "verifs": [],
            "grades": [],
            "proof_support": [],
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

def save_proof_support(paper, idx, proof_support):
    memory = load_memory(paper)
    while len(memory["proof_support"]) <= idx:
        memory["proof_support"].append("")
    memory["proof_support"][idx] = proof_support
    save_memory(paper, memory)

def get_proof_support(paper, idx):
    memory = load_memory(paper)
    if len(memory["proof_support"]) <= idx:
        return None
    return memory["proof_support"][idx]

def get_problem_statement(paper, idx):
    memory = load_memory(paper)
    if len(memory["statements"]) <= idx or memory["statements"][idx] == None:
        while len(memory["statements"]) <= idx:
            memory["statements"].append(None)
        statement = request([problem_statement_prompt + str(idx)], contents = [noproof(paper)])
        if statement == "NONE":
            return "NONE"
        memory["statements"][idx] = statement
        save_memory(paper, memory)
    return memory["statements"][idx]















































