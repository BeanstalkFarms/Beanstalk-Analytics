import logging
import time 
from collections import defaultdict

from serverless.utils_serverless import NotebookRunner

# disable logs 
logging.basicConfig(level=logging.CRITICAL)

num_iters = 3
nb_runner = NotebookRunner()

header = f"Notebook Runtime Analysis [{num_iters} iteration(s)]"
print(f"{'-'*len(header)}\n{header}\n{'-'*len(header)}\n")

runtimes = defaultdict(list)
for i in range(num_iters): 
    for nb_name in nb_runner.names: 
        start_time = time.time()
        nb_runner.execute(nb_name)
        run_secs = time.time() - start_time
        runtimes[nb_name].append(run_secs)
        
avg_runtimes = {k: sum(v) / len(v) for k, v in runtimes.items()}
for k in sorted(avg_runtimes, key=avg_runtimes.get): 
    fname = str(nb_runner.ntbk_name_path_map[k].name)
    print(f"Runtime of {fname:<40} | {avg_runtimes[k]:.2f} seconds.")
print(f"\nEstimated cumulative runtime: {sum(*avg_runtimes.values())}\n")
