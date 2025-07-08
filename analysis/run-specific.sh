python generate_stats.py --read=results_C.csv --write=stats_C.csv
python generate_stats.py --read=results_Si.csv --write=stats_Si.csv
python generate_stats.py --read=results_Ge.csv --write=stats_Ge.csv
python generate_stats.py --read=results_Sn.csv --write=stats_Sn.csv

python generate_figure_spearman.py --results=results_C.csv --mode=all
python generate_figure_spearman.py --results=results_Si.csv --mode=all
python generate_figure_spearman.py --results=results_Ge.csv --mode=all
python generate_figure_spearman.py --results=results_Sn.csv --mode=all

python generate_figure_kendall.py --results=results_C.csv --mode=all
python generate_figure_kendall.py --results=results_Si.csv --mode=all
python generate_figure_kendall.py --results=results_Ge.csv --mode=all
python generate_figure_kendall.py --results=results_Sn.csv --mode=all

python generate_topn_overlap.py --results=results_C.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_Si.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_Ge.csv --topns 5 10 25
python generate_topn_overlap.py --results=results_Sn.csv --topns 5 10 25
