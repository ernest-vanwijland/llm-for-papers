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
    tree_json: str
    ids: list
    toprove: dict
    name: dict
    depends_on: list
    ranking: list
    
    def __init__(self, paper, tree_json)

def build_tree(paper):
    tree_response = openai_request(prompt, paper = full(paper))
    beg = 0
    while tree_response[beg] != "{":
        beg += 1
    end = len(tree_response) - 1
    while tree_response[end] != "}":
        end -= 1
    tree_dict = json.loads(tree_response[beg:end+1])
    

tree_response = build_tree("2308.05208")


















































