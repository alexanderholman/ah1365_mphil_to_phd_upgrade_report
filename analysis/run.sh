#!/bin/bash

python generate_csv.py
python generate_csv.py --lower=C
python generate_csv.py --lower=Si
python generate_csv.py --lower=Ge
python generate_csv.py --lower=Sn
python generate_csv.py --upper=C
python generate_csv.py --upper=Si
python generate_csv.py --upper=Ge
python generate_csv.py --upper=Sn
python generate_csv.py --lower=C --upper=Si
python generate_csv.py --lower=Si --upper=C
python generate_csv.py --lower=Si --upper=Si
python generate_csv.py --lower=Si --upper=Ge
python generate_csv.py --lower=Si --upper=Sn
python generate_csv.py --lower=Ge --upper=Si
python generate_csv.py --lower=Ge --upper=Ge
python generate_csv.py --lower=Ge --upper=Sn
python generate_csv.py --lower=Sn --upper=Si
python generate_csv.py --lower=Sn --upper=Ge
python generate_csv.py --lower=Sn --upper=Sn
python generate_csv_perfect_alloys.py

python generate_stats.py --read=results.csv --write=stats.csv
python generate_stats.py --read=results_lower_C.csv --write=stats_lower_C.csv
python generate_stats.py --read=results_lower_C_upper_Si.csv --write=stats_lower_C_upper_Si.csv
python generate_stats.py --read=results_upper_C.csv --write=stats_upper_C.csv
python generate_stats.py --read=results_lower_Si.csv --write=stats_lower_Si.csv
python generate_stats.py --read=results_lower_Si_upper_C.csv --write=stats_lower_Si_upper_C.csv
python generate_stats.py --read=results_lower_Si_upper_Si.csv --write=stats_lower_Si_upper_Si.csv
python generate_stats.py --read=results_lower_Si_upper_Ge.csv --write=stats_lower_Si_upper_Ge.csv
python generate_stats.py --read=results_lower_Si_upper_Sn.csv --write=stats_lower_Si_upper_Sn.csv
python generate_stats.py --read=results_upper_Si.csv --write=stats_upper_Si.csv
python generate_stats.py --read=results_lower_Ge.csv --write=stats_lower_Ge.csv
python generate_stats.py --read=results_lower_Ge_upper_Si.csv --write=stats_lower_Ge_upper_Si.csv
python generate_stats.py --read=results_lower_Ge_upper_Ge.csv --write=stats_lower_Ge_upper_Ge.csv
python generate_stats.py --read=results_lower_Ge_upper_Sn.csv --write=stats_lower_Ge_upper_Sn.csv
python generate_stats.py --read=results_upper_Ge.csv --write=stats_upper_Ge.csv
python generate_stats.py --read=results_lower_Sn.csv --write=stats_lower_Sn.csv
python generate_stats.py --read=results_lower_Sn_upper_Si.csv --write=stats_lower_Sn_upper_Si.csv
python generate_stats.py --read=results_lower_Sn_upper_Ge.csv --write=stats_lower_Sn_upper_Ge.csv
python generate_stats.py --read=results_lower_Sn_upper_Sn.csv --write=stats_lower_Sn_upper_Sn.csv
python generate_stats.py --read=results_upper_Sn.csv --write=stats_upper_Sn.csv
python generate_stats.py --read=results_perfect_alloys.csv --write=stats_perfect_alloys.csv --dd-column=perfect_alloy_E_form_delta_dft@dft --dm-column=perfect_alloy_E_form_delta_dft@mlp --mm-column=perfect_alloy_E_form_delta_mlp@mlp --md-column=perfect_alloy_E_form_delta_mlp@dft

python generate_figure_spearman.py --results=results.csv --mode=all
python generate_figure_spearman.py --results=results_lower_C.csv --mode=all
python generate_figure_spearman.py --results=results_lower_C_upper_Si.csv --mode=all
python generate_figure_spearman.py --results=results_upper_C.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Si.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Si_upper_C.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Si_upper_Si.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Si_upper_Ge.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Si_upper_Sn.csv --mode=all
python generate_figure_spearman.py --results=results_upper_Si.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Ge.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Ge_upper_Si.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Ge_upper_Ge.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Ge_upper_Sn.csv --mode=all
python generate_figure_spearman.py --results=results_upper_Ge.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Sn.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Sn_upper_Si.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Sn_upper_Ge.csv --mode=all
python generate_figure_spearman.py --results=results_lower_Sn_upper_Sn.csv --mode=all
python generate_figure_spearman.py --results=results_upper_Sn.csv --mode=all
python generate_figure_spearman.py --results=results_perfect_alloys.csv --mode=all

python generate_figure_kendall.py --results=results.csv --mode=all
python generate_figure_kendall.py --results=results_lower_C.csv --mode=all
python generate_figure_kendall.py --results=results_lower_C_upper_Si.csv --mode=all
python generate_figure_kendall.py --results=results_upper_C.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Si.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Si_upper_C.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Si_upper_Si.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Si_upper_Ge.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Si_upper_Sn.csv --mode=all
python generate_figure_kendall.py --results=results_upper_Si.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Ge.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Ge_upper_Si.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Ge_upper_Ge.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Ge_upper_Sn.csv --mode=all
python generate_figure_kendall.py --results=results_upper_Ge.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Sn.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Sn_upper_Si.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Sn_upper_Ge.csv --mode=all
python generate_figure_kendall.py --results=results_lower_Sn_upper_Sn.csv --mode=all
python generate_figure_kendall.py --results=results_upper_Sn.csv --mode=all
python generate_figure_kendall.py --results=results_perfect_alloys.csv --mode=all

python generate_topn_overlap.py --results=results.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_C.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_C_upper_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_upper_C.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Si_upper_C.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Si_upper_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Si_upper_Ge.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Si_upper_Sn.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_upper_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Ge.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Ge_upper_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Ge_upper_Ge.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Ge_upper_Sn.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_upper_Ge.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Sn.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Sn_upper_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Sn_upper_Ge.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_lower_Sn_upper_Sn.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_upper_Sn.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_perfect_alloys.csv --topns 5 10 25