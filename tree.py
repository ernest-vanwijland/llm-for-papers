from api import *
from memory_util import *
import json

build_tree_prompt = f"""
You are an expert research assistant specializing in parsing mathematical literature. Your task is to analyze the provided mathematical article and generate a dependency tree of its formal statements.

## Goal
Read the text and identify all **Definitions, Theorems, Lemmas, Propositions, Corollaries, Claims, and Facts**. For each statement, determine which other statements it explicitly relies upon in its proof or formulation.

## Output Format
The output MUST be a single, valid JSON object. This object will contain a single key, "statements", which is a list of statement objects. Do not include any text, explanations, or code formatting before or after the JSON object.

Each statement object in the list must conform to the following JSON structure:
{{
"statements" = [{{
  "id": int,
  "name": str,
  "depends_on": [int, ...]
}}
]
}}
"""

find_toprove_prompt = f"""
You are an expert research assistant specializing in parsing mathematical literature. Your task is to analyze the provided mathematical article and generate the correspondence between the statements and the TOPROVE indices.

## Goal
Read the text and identify all the TOPROVE. For each one, determine which statement in the paper it replaced the proof of. You need to find the correspondence between each TOPROVE id, and the name of the statement it replaced the proof of. You just need to identify the name of the statement (i.e. Lemma 2.4, Proposition 5, etc.), not the body of the statement.

## Output Format
The output MUST be a single, valid JSON object. This object will contain a single key, "toproves", which is a list of toprove objects. Do not include any text, explanations, or code fromatting before or after the JSON object.

Each statement object in the list must conform to the following JSON structure:
{{
"toproves" = [{{
  "toprove_id": int,
  "statement": str
}}
]
}}
"""

find_external_refs = """
You are an expert research assistant specializing in parsing mathematical literature. Your task is to analyze the provided mathematical article and generate the list of external references from other papers that are used in the proofs but that are not reintroduced in the paper.

## Goal
Read the text and identify all the external references that are not reintroduced in the paper. For each of them, extract the sentence that references it from the paper, and the name of the claim it is used to prove (for example "Lemma 3" or "Proposition 2.2"), make sure you don't add extra words like "Proof of Lemma 3". For the format of the reference sentence, use latex for mathematical notations.

## Output Format
The output MUST be a single, valid JSON object. This object will contain a single key, "references", which is a list of reference objects. Do not include any text, explanations, or code formatting before or after the JSON object.

Each reference object in the list must conform to the following JSON structure:
{{
"references" = [{{
  "claim_name": str,
  "reference_sentence": str
}}
]
}}
"""

def get_dict(json_str):
    beg = 0
    while json_str[beg] != "{":
        beg += 1
    end = len(json_str) - 1
    while json_str[end] != "}":
        end -= 1
    dct = json.loads(json_str[beg:end+1])
    return dct

class Tree:
    paper: str
    tree_dict: str
    ids: list
    toprove: dict
    name: dict
    depends_on: dict
    ranking: dict
    references: dict
    
    def print(self):
        print(self.paper)
        print(self.ids)
        print(self.name)
        print(self.toprove)
        print(self.depends_on)
        print(self.ranking)
        print(self.references)
    
    def build_tree(self, paper):
        tree_file = f"memory/tree_{paper}.json"
        if not os.path.exists(tree_file):
            print(f"Loading tree of {paper}.")
            tree_response = request(build_tree_prompt, files = [full(paper)])
            tree_dict = get_dict(tree_response)
            
            toprove_response = request(find_toprove_prompt, files=[noproof(paper)])
            toprove_dict = get_dict(toprove_response)
            
            for tp in toprove_dict["toproves"]:
                for statement in tree_dict["statements"]:
                    if statement["name"] == tp["statement"]:
                        statement["toprove"] = tp["toprove_id"]
            for statement in tree_dict["statements"]:
                if "toprove" not in statement.keys():
                    statement["toprove"] = -1
            
            refs_dict = get_dict(request(find_external_refs, files=[full(paper)]))
            for statement in tree_dict["statements"]:
                statement["references"] = []
            for ref in refs_dict["references"]:
                for statement in tree_dict["statements"]:
                    if statement["name"] == ref["claim_name"]:
                        statement["references"].append(ref["reference_sentence"])
            
            with open(tree_file, 'w', encoding='utf-8') as f:
                json.dump(tree_dict, f, indent=2, ensure_ascii=False)
            return tree_dict
        else:
            with open(tree_file, 'r', encoding='utf-8') as f:
                tree_dict = json.load(f)
            return tree_dict
    
    def __init__(self, paper):
        self.paper = paper
        self.tree_dict = self.build_tree(paper)
        self.ids, self.toprove, self.name, self.depends_on, self.ranking, self.references = [], {}, {}, {}, {}, {}
        for statement in self.tree_dict["statements"]:
            id = statement["id"]
            self.ids.append(id)
            self.name[id] = statement["name"]
            self.depends_on[id] = statement["depends_on"]
            self.toprove[id] = statement["toprove"]
            self.ranking[id] = -1
            self.references[id] = statement["references"]
        for level in range(len(self.ids)):
            for id in self.ids:
                parents_done = True
                for p in self.depends_on[id]:
                    if self.ranking[p] == -1:
                        parents_done = False
                if parents_done and self.ranking[id] == -1:
                    self.ranking[id] = level

def get_id(tree, idx):
    for id in tree.ids:
        if tree.toprove[id] == idx:
            return id
    return -1




































































































