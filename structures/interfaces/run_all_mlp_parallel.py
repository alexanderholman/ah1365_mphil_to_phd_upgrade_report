import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 1  # Adjust this to the number of parallel jobs you want to run

def should_run(directory):
    return os.path.isdir(directory) and not os.path.isfile(os.path.join(directory, "OUTCAR_MLP_MACE"))

def run_job(directory):
    try:
        print(f"[START] {directory}")
        env = os.environ.copy()
        env["PATH"] = "/bin:" + env["PATH"]  # Or ~/bin if that's where the script is
        result = subprocess.run(
            ["bash", "run_mlp.sh"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"[ERROR] {directory}:\n{result.stderr}")
        else:
            print(f"[DONE]  {directory}")
    except Exception as e:
        print(f"[EXCEPTION] {directory}: {e}")

if __name__ == "__main__":
    dirs = [d for d in os.listdir(".") if should_run(d)]

    print(f"Running run_mlp.sh in {len(dirs)} directories with up to {MAX_WORKERS} workers...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_job, d): d for d in dirs}
        for future in as_completed(futures):
            pass
