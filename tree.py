from api import *
from memory_util import *
import json

prompt = f"""
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

class Tree:
    paper: str
    tree_dict: str
    ids: list
    toprove: dict
    name: dict
    depends_on: dict
    ranking: dict
    
    def print(self):
        print(self.paper)
        print(self.ids)
        print(self.name)
        print(self.toprove)
        print(self.depends_on)
        print(self.ranking)
    
    def build_tree(self, paper):
        tree_response = request([prompt], contents = [full(paper)])
        beg = 0
        while tree_response[beg] != "{":
            beg += 1
        end = len(tree_response) - 1
        while tree_response[end] != "}":
            end -= 1
        tree_dict = json.loads(tree_response[beg:end+1])
        return tree_dict
    
    def __init__(self, paper):
        self.paper = paper
        self.tree_dict = self.build_tree(paper)
        self.ids, self.toprove, self.name, self.depends_on, self.ranking = [], {}, {}, {}, {}
        for statement in self.tree_dict["statements"]:
            id = statement["id"]
            self.ids.append(id)
            self.name[id] = statement["name"]
            self.depends_on[id] = statement["depends_on"]
            self.toprove[id] = -1
            self.ranking[id] = -1
        for level in range(len(self.ids)):
            for id in self.ids:
                parents_done = True
                for p in self.depends_on[id]:
                    if self.ranking[p] == -1:
                        parents_done = False
                if parents_done and self.ranking[id] == -1:
                    self.ranking[id] = level

tree = Tree("2308.05208")
tree.print()


































































































