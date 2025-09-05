import regex as re
import os
import sys
import tarfile
import shutil
import subprocess
import tempfile
from typing import Optional
from pathlib import Path

class ProofReplacer:
    def __init__(self):
        self.counter = 0

    def __call__(self, match: re.Match) -> str:
        self.counter += 1
        # The recursive regex pattern captures the start and end tags in groups 1 and 3
        start_tag = match.group(1)
        end_tag = match.group(3)
        return f"{start_tag}\\textcolor{{red}}{{TOPROVE {self.counter-1}}}{end_tag}"

# Create a single, global instance to manage the counter's state.
proof_replacer_instance = ProofReplacer()

def remove_proofs_from_tex(file_path: str, project_root_path: str) -> None:
    proof_replacer_instance.counter = 0
    
    input_path = Path(file_path)
    project_root = Path(project_root_path)
    
    if not input_path.is_file():
        raise FileNotFoundError(f"Error: Input file not found at '{input_path}'")

    # Determine the file's path relative to the project's root directory.
    relative_path = input_path.relative_to(project_root)
    
    # Construct the correct output path inside the single 'noproof' folder.
    output_root_dir = project_root / 'noproof'
    output_path = output_root_dir / relative_path

    # Ensure the destination subdirectory exists before writing the file.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if input_path.suffix!= '.tex':
            shutil.copy(input_path, output_path)
            return

        with open(input_path, 'r', encoding='utf-8') as infile:
            content = infile.read()
        
        # Step 1: Isolate and protect commented-out blocks
        commented_blocks = []
        comment_pattern = re.compile(
            r"(\\begin{comment}.*?\\end{comment}|\\iffalse.*?\\fi)",
            flags=re.DOTALL
        )

        def protect_comment_block(match):
            commented_blocks.append(match.group(0))
            return f"__COMMENT_BLOCK_{len(commented_blocks) - 1}__"

        content_without_comments = comment_pattern.sub(protect_comment_block, content)

        # Step 2: Process proofs on the "active" content
        proof_pattern = re.compile(
            r"(\\begin{proof})"
            r"((?:(?!\\begin{proof}|\\end{proof}).|(?R))*)"
            r"(\\end{proof})",
            flags=re.DOTALL
        )
        
        modified_content = proof_pattern.sub(proof_replacer_instance, content_without_comments)

        # Step 3: Restore the commented-out blocks
        final_content = modified_content
        for i, block in enumerate(commented_blocks):
            final_content = final_content.replace(f"__COMMENT_BLOCK_{i}__", block)

        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(final_content)
        
    except IOError as e:
        print(f"An I/O error occurred: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

def extract_archive(archive_path: str):
    """
    Extracts a.tar.gz file with a name like '*-XXXX.XXXXX*.tar.gz'
    into a folder named 'XXXX.XXXXX' and returns the path to that folder.
    """
    input_path = Path(archive_path)
    
    # Regex to find the required part of the filename
    pattern = re.compile(r'-(\d{4}\.\d{5}).*\.tar\.gz$')
    match = pattern.search(input_path.name)

    if not match:
        print(f"Error: Filename '{input_path.name}' does not match the expected '*-XXXX.XXXXX*.tar.gz' format.", file=sys.stderr)
        return None

    folder_name = match.group(1)
    output_dir = input_path.parent / folder_name
    
    try:
        #print(f"Extracting '{input_path.name}' to '{output_dir}'...")
        output_dir.mkdir(exist_ok=True)
        with tarfile.open(input_path, "r:gz") as tar:
            tar.extractall(path=output_dir)
        #print("Extraction complete.")
        return str(output_dir)
    except tarfile.TarError as e:
        print(f"Error extracting archive: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}", file=sys.stderr)
        return None

def find_archives_in_folder(folder_path: str):
    """
    Finds all.tar.gz files in the specified folder and returns a list of their paths.
    """
    input_dir = Path(folder_path)
    if not input_dir.is_dir():
        print(f"Error: Not a valid directory: '{folder_path}'", file=sys.stderr)
        return
    
    # Use glob to find all files ending with.tar.gz in the directory
    archive_files = [str(p) for p in input_dir.glob('*.tar.gz')]
    return archive_files

def inline_latex_files(folder_path: str, main_file_name: str) -> Optional[str]:
    # 1. Check if latexpand is installed and available in the system's PATH.
    if not shutil.which("latexpand"):
        print(
            "Error: 'latexpand' command not found.",
            "Please ensure you have a full TeX distribution (like TeX Live or MiKTeX) installed.",
            file=sys.stderr
        )
        return None

    # 2. Set up paths using pathlib for robustness.
    source_dir = Path(folder_path).resolve()
    main_file = source_dir / main_file_name
    
    if not main_file.is_file():
        print(f"Error: Main file not found at '{main_file}'", file=sys.stderr)
        return None

    # Define the output filename for the flattened file.
    output_filename = "main_expanded.tex"
    output_path = source_dir / output_filename

    # 3. Construct the command to run latexpand.
    # The -o flag specifies the output file.
    command = [
        "latexpand",
        "--output",
        output_filename,
        main_file_name
    ]

    #print(f"Running latexpand on '{main_file_name}'...")

    # 4. Execute the command.
    try:
        # We run the command with the current working directory set to the source
        # folder, so that latexpand can find all the included files.
        process = subprocess.run(
            command,
            cwd=source_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        #print(f"Successfully created inlined file: {output_path}")
        return str(output_path)
        
    except subprocess.CalledProcessError as e:
        print("--- LATEXPAND FAILED ---", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print("\n--- STDOUT ---", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print("\n--- STDERR ---", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return None

def find_main_file(folder_path: str) -> Optional[str]:
    input_dir = Path(folder_path)
    if not input_dir.is_dir():
        print(f"Error: Provided path '{folder_path}' is not a valid directory.", file=sys.stderr)
        return None

    # Iterate through all files with a.tex extension in the folder
    for tex_file in input_dir.glob('*.tex'):
        try:
            # Read the content of the file, ignoring potential encoding errors
            content = tex_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check if the file contains the target string, which marks the main document
            if r'\begin{document}' in content:
                #print(f"Found main document file: {tex_file}")
                return str(tex_file)
        except IOError as e:
            print(f"Error reading file {tex_file}: {e}", file=sys.stderr)
            # Continue to the next file if one is unreadable
            continue

    print("No file containing '\\begin{document}' was found in the folder.")
    return None

def process_folder(folder_path: str) -> None:
    input_dir = Path(folder_path)
    if not input_dir.is_dir():
        print(f"Error: Input path is not a valid directory: '{input_dir}'", file=sys.stderr)
        return
    
    old_main_file = Path(find_main_file(folder_path))
    #print(old_main_file.name)
    inline_latex_files(folder_path, old_main_file.name)
    main_file = "main_expanded.tex"
    
    #print(f"Processing all files in directory: {input_dir}")
    # Use rglob to recursively find all items
    for item_path in input_dir.rglob('*'):
        # Skip any files that are already in a 'noproof' directory to avoid recursion
        if 'noproof' in item_path.parts:
            continue

        # Process only if it's a file
        if item_path.is_file():
            try:
                remove_proofs_from_tex(str(item_path), folder_path)
            except Exception as e:
                print(f"Error processing file {item_path}: {e}", file=sys.stderr)

def process(archive):
    extracted = extract_archive(archive)
    process_folder(extracted)
    main_file = "main_expanded.tex"
    compile_latex_to_pdf(extracted, main_file)
    compile_latex_to_pdf(extracted + "/noproof", main_file)

def compile_latex_to_pdf(source_folder: str, main_filename: str) -> None:
    """
    Compiles a LaTeX document using pdflatex, ensuring an existing.bbl file is used.
    """
    pdflatex_path = shutil.which("pdflatex")
    if not pdflatex_path:
        print("Error: pdflatex command not found.", file=sys.stderr)
        print("Please ensure a TeX distribution (like TeX Live, MiKTeX) is installed.", file=sys.stderr)
        return

    src_path = Path(source_folder)
    job_name = "paper"

    # Find any existing.bbl file and rename it to match the jobname.
    bbl_files = list(src_path.glob('*.bbl'))
    if bbl_files:
        # Get the first file from the list of found.bbl files
        original_bbl_path = bbl_files[0]
        expected_bbl_path = src_path / f"{job_name}.bbl"
        if original_bbl_path!= expected_bbl_path:
            #print(f"Found '{original_bbl_path.name}'. Renaming to '{expected_bbl_path.name}' for compilation.")
            shutil.move(original_bbl_path, expected_bbl_path)

    pdflatex_cmd = [
        pdflatex_path,
        "-interaction=nonstopmode",
        f"-jobname={job_name}",
        main_filename
    ]
    
    #print(f"Compiling {main_filename} in {src_path}...")
    
    try:
        # Run pdflatex three times to ensure all references and the bibliography are correctly included.
        for i in range(3):
            #print(f"Running pdflatex (pass {i+1})...")
            subprocess.run(pdflatex_cmd, cwd=src_path, capture_output=True, text=True, check=True)

        #print(f"Successfully compiled. Output is at {src_path / (job_name + '.pdf')}")
    except subprocess.CalledProcessError as e:
        print(f"--- COMPILATION FAILED during '{' '.join(e.cmd)}' ---", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print("\n--- STDOUT/LOG ---", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print("\n--- STDERR ---", file=sys.stderr)
        print(e.stderr, file=sys.stderr)

if __name__ == '__main__':
    folder = "data"
    papers = find_archives_in_folder(folder)
    cnt = 0
    for paper in papers:
        print(f"Preparing paper {cnt + 1} / {len(papers)}")
        cnt += 1
        process(paper)





























































