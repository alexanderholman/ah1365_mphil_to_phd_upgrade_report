#!/usr/bin/env python3
import argparse

# Setup scripts
from scripts.setup.jobs_mlp_mace import main as setup_mlp_mace_jobs_main
from scripts.setup.jobs_dft_vasp import main as setup_dft_vasp_jobs_main
from scripts.setup.structure_data_json_files import main as setup_structure_main

# Run scripts
from scripts.run.structure_data_concat import main as run_concat_main
from scripts.run.submit_mlp_mace_jobs import main as submit_mlp_mace_jobs_main
from scripts.run.submit_dft_vasp_jobs import main as submit_dft_vasp_jobs_main

# Cleanup scripts
from scripts.cleanup.structure_data_files import main as cleanup_structure_main
from scripts.cleanup.jobs_mlp_mace_files import main as cleanup_mlp_mace_jobs_main
from scripts.cleanup.jobs_dft_vasp_files import main as cleanup_dft_vasp_jobs_main

def main():
    parser = argparse.ArgumentParser(description="Artemis Utilities Manager")
    # Setup scripts
    parser.add_argument("--setup-mlp-mace-jobs", action="store_true", help="Setup MLP MACE SBATCH and run-mace.py files")
    parser.add_argument("--setup-dft-vasp-jobs", action="store_true", help="Setup DFT VASP SBATCH files")
    parser.add_argument("--setup-jobs", action="store_true", help="Setup SBATCH (MLP MACE and DFT VASP) and run-mace.py files")
    parser.add_argument("--setup-structure", action="store_true", help="Setup concat_artemis_data.py next to POSCARs")
    parser.add_argument("--setup-all", action="store_true", help="Full setup: jobs + structure + concat")
    # Run scripts
    parser.add_argument("--run-concat", action="store_true", help="Run structure data concat scripts")
    parser.add_argument("--submit-mlp-mace-jobs", action="store_true", help="Submit sbatch MLP MACE jobs")
    parser.add_argument("--submit-dft-vasp-jobs", action="store_true", help="Submit sbatch DFT VASP jobs")
    parser.add_argument("--submit-jobs", action="store_true", help="Submit all sbatch jobs")
    # Cleanup
    parser.add_argument("--cleanup-structure", action="store_true", help="Cleanup concat scripts and poscar_data.json files")
    parser.add_argument("--cleanup-mlp-mace-jobs", action="store_true", help="Cleanup MLP MACE SBATCH and run-mace.py setup files")
    parser.add_argument("--cleanup-dft-vasp-jobs", action="store_true", help="Cleanup DFT VASP SBATCH setup files")
    parser.add_argument("--cleanup-jobs", action="store_true", help="Cleanup SBATCH (MLP MACE and DFT VASP) and run-mace.py setup files")
    parser.add_argument("--cleanup-all", action="store_true", help="Full cleanup: delete concat and poscar_data.json files")
    # Full run
    parser.add_argument("--all", action="store_true", help="Full run: full setup + submit jobs")

    args = parser.parse_args()

    # Setup scripts
    # Setup Jobs
    if args.setup_mlp_mace_jobs:
        setup_mlp_mace_jobs_main()
    if args.setup_dft_vasp_jobs:
        setup_dft_vasp_jobs_main()
    if args.setup_jobs:
        setup_mlp_mace_jobs_main()
        setup_dft_vasp_jobs_main()
    # Setup Structure
    if args.setup_structure:
        setup_structure_main()
    # Setup all
    if args.setup_all:
        setup_mlp_mace_jobs_main()
        setup_dft_vasp_jobs_main()
        setup_structure_main()

    # Run scripts
    if args.run_concat:
        run_concat_main()

    # Submit jobs
    if args.submit_mlp_mace_jobs:
        submit_mlp_mace_jobs_main()
    if args.submit_dft_vasp_jobs:
        submit_dft_vasp_jobs_main()
    if args.submit_jobs:
        submit_mlp_mace_jobs_main()
        submit_dft_vasp_jobs_main()

    # Cleanup scripts
    # Cleanup jobs
    if args.cleanup_mlp_mace_jobs:
        cleanup_mlp_mace_jobs_main()
    if args.cleanup_dft_vasp_jobs:
        cleanup_dft_vasp_jobs_main()
    if args.cleanup_jobs:
        cleanup_mlp_mace_jobs_main()
        cleanup_dft_vasp_jobs_main()
    # Cleanup structure
    if args.cleanup_structure:
        cleanup_structure_main()
    # Cleanup all
    if args.cleanup_all:
        cleanup_mlp_mace_jobs_main()
        cleanup_dft_vasp_jobs_main()
        cleanup_structure_main()

    # Run all in order
    if args.all:
        cleanup_mlp_mace_jobs_main()
        cleanup_dft_vasp_jobs_main()
        cleanup_structure_main()
        setup_mlp_mace_jobs_main()
        setup_dft_vasp_jobs_main()
        setup_structure_main()
        run_concat_main()
        # submit_mlp_mace_jobs_main()
        # submit_dft_vasp_jobs_main()

    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main()
