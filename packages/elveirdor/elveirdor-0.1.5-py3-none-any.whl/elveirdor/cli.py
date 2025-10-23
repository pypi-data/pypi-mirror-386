from elveirdor.core.engine import ElveirdorEngine
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--grid", type=int, default=20)
    p.add_argument("--text", type=str, default="ELVEIRDOR")
    p.add_argument("--export", type=str, default="output.png")
    p.add_argument("--sequence", type=str)
    args = p.parse_args()
    engine = ElveirdorEngine(grid_size=args.grid)
    engine.run(text=args.text, sequence=args.sequence, output=args.export)

if __name__ == "__main__":
    main()
