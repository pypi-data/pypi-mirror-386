from elveirdor.pipeline import run_elveirdor_pipeline
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run the ELVEIRDOR Infinity Computing pipeline.")
    parser.add_argument("--text", type=str, default="ELVEIRDOR")
    parser.add_argument("--grid", type=int, default=10)
    parser.add_argument("--export", type=str, default="output.png")
    parser.add_argument("--sequence", type=str, default="3 1 18 18 15 20")
    args = parser.parse_args()
    run_elveirdor_pipeline(grid_size=args.grid, output_filename=args.export, text=args.text, sequence=args.sequence)

if __name__ == "__main__":
    main()
