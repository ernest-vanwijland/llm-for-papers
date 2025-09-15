import os
import glob
from verifier import *
from test import *

def replace_antislash(filename):
    new_filename = ""
    for i in filename:
        if i != "\\":
            new_filename += i
        else:
            new_filename += "/"
    return new_filename

def get_checker_name(filename):
    filename = os.path.basename(filename)
    if filename[0] == "a":
        after = filename.split("results_")[1]
        before = after.split(".")[0]
        last_underscore = 0
        for i in range(len(before) - 1, -1, -1):
            if before[i] == "_":
                last_underscore = i
                break
        return before[:last_underscore]
    elif filename[0] == "r":
        cnt = 0
        buff = ""
        for i in filename:
            if cnt >= 3:
                if i == ".":
                    return buff
                buff += i
            elif i == "_":
                cnt += 1
        return "NOT_FOUND"
    return "NOT_FOUND"

def print_results(checker_name, results):
    print("---------------------------------------------")
    print(f"Here are the results for checker: {checker_name}")
    correct = results["truepositives"]["all"] + results["truenegatives"]["all"]
    print(f"The verdict was correct in {correct} out of {results['total']['all']} cases.")
    print(f"There were {results['truepositives']['all']} out of {results['truepositives']['positive']} true positives.")
    print(f"There were {results['truenegatives']['all']} out of {results['truenegatives']['negative']} true negatives.")
    print("Here are the results per category:")
    for cat in ["original", "paraphrase", "switch"]:
        print(f"{cat}: {results['truepositives'][cat]} / {results['total'][cat]} true positives.")
    for cat in ["error", "incomplete", "hallucination"]:
        print(f"{cat}: {results['truenegatives'][cat]} / {results['total'][cat]} true negatives.")
    print("---------------------------------------------")

def compile_results(CHECKER = None):
    checker_name = CHECKER.__name__
    all_result_files = glob.glob("results/*")
    result_files = []
    for filename in all_result_files:
        if filename in glob.glob(f"results/*{checker_name}*"):
            result_files.append(filename)
    results = {
        "total": {
            "all": 0,
            "original": 0,
            "paraphrase": 0,
            "switch": 0,
            "error": 0,
            "incomplete": 0,
            "hallucination": 0
        },
        "truepositives": {
            "positive": 0,
            "all": 0,
            "original": 0,
            "paraphrase": 0,
            "switch": 0
        },
        "truenegatives": {
            "negative": 0,
            "all": 0,
            "error": 0,
            "incomplete": 0,
            "hallucination": 0
        }
    }
    for filename in result_files:
        for testcase_file, verdict in load_testcase(filename).items():
            testcase = load_testcase(replace_antislash(testcase_file))
            if testcase == None :
                continue
            results["total"]["all"] += 1
            results["total"][testcase["comment"]] += 1
            if testcase["validity"] == 1:
                results["truepositives"]["positive"] += 1
                if verdict == 1:
                    results["truepositives"]["all"] += 1
                    results["truepositives"][testcase["comment"]] += 1
            else:
                results["truenegatives"]["negative"] += 1
                if verdict == 0:
                    results["truenegatives"]["all"] += 1
                    results["truenegatives"][testcase["comment"]] += 1
    
    print_results(checker_name, results)
















































