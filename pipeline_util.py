from api import *
from prompts import *
import json

def full(paper):
    return f"data/{paper}/paper.pdf"

def noproof(paper):
    return f"data/{paper}/noproof/paper.pdf"

def save_memory(memory_file, memory):
    memory["timestamp"] = __import__('datetime').datetime.now().isoformat()
    try:
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
        print(f"Memory saved to {memory_file}")
        return True
    except Exception as e:
        print(f"Error saving memory to {memory_file}: {e}")
        return False

def load_memory(memory_file):
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory = json.load(f)
        print(f"Memory loaded from {memory_file}")
        return memory
    except Exception as e:
        print(f"Error loading memory from {memory_file}: {e}")
        return None

def extract_detailed_solution(solution, marker='Detailed Solution', after=True):
    return solution
    idx = solution.find(marker)
    if idx == -1:
        return ''
    if after:
        return solution[idx.len(marker):].strip()
    else:
        return solution[:idx].strip()

def get_solution(idx, memory):
    if len(memory["solutions"]) <= idx:
        return None
    return memory["solutions"][idx]

def save_solution(idx, solution, memory):
    while len(memory["solutions"]) <= idx:
        memory["solutions"].append("")
    memory["solutions"][idx] = solution

def save_verif(idx, verif, memory):
    while len(memory["verifs"]) <= idx:
        memory["verifs"].append("")
    memory["verifs"][idx] = verif

def save_grade(idx, grade, memory):
    while len(memory["grades"]) <= idx:
        memory["grades"].append(-1)
    memory["grades"][idx] = grade

def get_verif(idx, memory):
    if len(memory["verifs"]) <= idx:
        return None
    return memory["verifs"][idx]

def get_problem_statement(paper, idx, memory_file):
    memory = load_memory(memory_file)
    if len(memory["statements"]) <= idx or memory["statements"][idx] == None:
        while len(memory["statements"]) <= idx:
            memory["statements"].append(None)
        statement = request([problem_statement_prompt + str(idx)], contents = [noproof(paper)])
        if statement == "NONE":
            return "NONE"
        memory["statements"][idx] = statement
        save_memory(memory_file, memory)
    return memory["statements"][idx]

def load_problem_statements(paper, memory_file):
    idx = 0
    while get_problem_statement(paper, idx, memory_file) != "NONE" and idx < 100:
        idx += 1
    if idx == 100:
        print("Too many TOPROVE, there must be a problem.")

def agent(paper, idx, memory_file=None, resume_from_memory=False):
    if resume_from_memory and memory_file:
        memory = load_memory(memory_file)
        if memory:
            statements = memory.get("statements", problem_statement)





































