import subprocess
import psutil
import time
import pandas as pd
import matplotlib.pyplot as plt
from typing import List

binfile = "count_tc"
tgt_dir = "/home/chen/projects/rust/" 


cmd_str = (f"/home/chen/projects/code_stats/target/debug/{binfile} "
           f"-t rs -t c -f {tgt_dir}")

def start_process(cmd_str):
    subprocess.run(
        ['sudo', 'bash', '-c', 'sync;echo 3 > /proc/sys/vm/drop_caches']
    ).check_returncode()
    proc = subprocess.Popen(
        ['bash', '-c', cmd_str],
        encoding='utf-8',
        stdout=subprocess.PIPE)
    return proc

def bench_once(cmd_str):
    HIST_INTERVAL = 0.1 # seconds
    process = start_process(cmd_str)
    proc = psutil.Process(process.pid)

    history = []
    count = 0
    while process.poll() is None:
        history.append([
            count * HIST_INTERVAL,
            proc.memory_percent(),
            proc.cpu_percent(),
            proc.num_threads(),
            proc.num_fds()
        ])
        count += 1
        time.sleep(HIST_INTERVAL)

    (out_data, _) = process.communicate()
    totaltime = out_data.splitlines()[1].split(":")[1].strip()[:-1]

    hist_df = pd.DataFrame(history, columns=['time-secs', 'mem-percent', 'cpu-percent', 'threads-num', 'file-descs'])
    summary = {
        "total-time": totaltime,
        "cpu%-mean": hist_df['cpu-percent'].mean(),
        "mem%-mean": hist_df['mem-percent'].mean(),
        "file-med": hist_df['file-descs'].median(),
        "thrd-med": hist_df['threads-num'].median(),
    }
    return summary, hist_df


def bench_binaries(binaries: List[str]):
    summaries = dict()
    hist_dfs = dict()
    for binary in binaries:
        cmd_str = (f"/home/chen/projects/code_stats/target/release/{binary} "
                   f"-t rs -t c -f {tgt_dir}")
        summary, hist = bench_once(cmd_str)
        summaries[binary] = summary
        hist_dfs[binary] = hist
    return summaries, hist_dfs


if __name__ == "__main__":
    # summary, hist = bench_once(cmd_str)
    # print(summary)
    # hist.to_csv("hist.csv", index=False)
    # hist['cpu-percent'].plot()
    # plt.savefig("cpu_percent.png", dpi=300)

    binaries = ['count_tc', 'count_notc']
    summaries, hist_dfs = bench_binaries(binaries)
    print(summaries)
    for bfile, df in hist_dfs.items():
        df.to_csv(f"{bfile}.csv", index=False)
