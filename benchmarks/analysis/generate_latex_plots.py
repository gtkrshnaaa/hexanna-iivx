import os
import matplotlib.pyplot as plt

def generate_benchmark_figures(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    scale_factors = [1, 5, 10]
    hexanna_rss = [412, 488, 524]
    pandas_rss = [2450, 9820, 11900]

    plt.figure(figsize=(7, 4.5))
    plt.plot(scale_factors, hexanna_rss, marker='s', color='#1f77b4', linewidth=2, label='Hexanna IIVX (Bounded)')
    plt.plot(scale_factors, pandas_rss, marker='^', color='#d62728', linewidth=2, linestyle='--', label='Pandas-Based Agent (In-Memory)')

    plt.title("Peak RAM Footprint (RSS) Under Expanding Workload Scales", fontsize=11, fontweight='bold')
    plt.xlabel("TPC-H Scale Factor (~GB)", fontsize=10)
    plt.ylabel("Peak RSS Memory (MB)", fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    fig_path = os.path.join(output_dir, "memory_comparison_plot.pdf")
    plt.savefig(fig_path, format="pdf")
    print(f"[*] Generated publication vector figure at: {fig_path}")

if __name__ == "__main__":
    generate_benchmark_figures("paper/figures")
