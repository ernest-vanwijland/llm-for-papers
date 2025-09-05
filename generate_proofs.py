from pipeline import *
from pipeline_util import *
from api import *
from checker import *

def get_proof(paper, idx, memory_file):
    """ returns proof of TOPROVE idx from the full paper """
    memory = load_memory(memory_file)
    prompt = f"Your job is to extract the proof of TOPROVE {idx} from the attached paper. The proof might be a single paragraph, or it might span multiple pages. You need to be careful to extract the entire proof and nothing else. The proof starts right after the statement of the theorem/lemma it proves, and ends with a QED symbol (like a square) or with the beginning of a new section. Just output the proof using latex notation for mathematical characters, and nothing else."
    proof = request([prompt], contents=[full(paper), noproof(paper)])
    save_memory(memory_file, memory)
    return proof



if __name__ == "__main__":
    memory_file = "memory.json"
    papers = list_papers("data/")
    
    paper = "2407.02412"
    
    #verify_solution(paper, 0, memory_file)
    
    print(get_proof(paper, 2, memory_file))