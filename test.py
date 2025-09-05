from api import *





if __name__ == "__main__":
    run_examples()
    prompt = "You are a university professor and an expert mathematician and algorithmician. Your job is to write the proof where TOPROVE 1 is written. Do not read the article after that point. You need to understand the article until TOPROVE 1 to understand what the claim to prove is. Make sure your proof is rigorous and correctly proves the desired claim. Your proof cannot use the statement of the claim it needs to prove to prove itself, and it cannot use any element that is not yet proved. Provide your answer as a Latex code snippet that I can copy paste into an overleaf document, make sure it compiles correctly. Just provide the proof of TOPROVE 1 and nothing else."
    
    prompt = "You are a university professor and an expert mathematician and algorithmician. Your job is to understand the article until TOPROVE 1, do not read anything that comes after. Then, you need to output a latex code snippet that compiles correctly that contains just the statement of the result of which TOPROVE 1 replaces the proof, and nothing else."
    
    
    files=["data/2407.02412/noproof/paper.pdf"]
    
    if os.path.exists(files[0]):
        text_response = request(prompt, contents = files)
        print(text_response)
    else:
        print(f"File not found")
