# Simple CLI entry point
import argparse
import json
from .pipeline import run_pipeline

def build_parser():
    p = argparse.ArgumentParser(prog='elveirdor')
    p.add_argument('--text', type=str, default='Infinity Mosaic',
                   help='Text to encode')
    p.add_argument('--grid', type=int, default=16,
                   help='Grid size')
    p.add_argument('--seed', type=int, default=12345,
                   help='Random seed')
    p.add_argument('--sequence', type=str, nargs='*',
                   help='Pipeline steps to run')
    p.add_argument('--x', type=int, default=None,
                   help='X position for draw_m (defaults to center)')
    p.add_argument('--y', type=int, default=None,
                   help='Y position for draw_m (defaults to center)')
    p.add_argument('--scale', type=int, default=1,
                   help='Scale factor for draw_m (default=1)')
    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    metadata, _ = run_pipeline(
        text=args.text,
        grid_size=args.grid,
        seed=args.seed,
        sequence=args.sequence,
        x=args.x,
        y=args.y,
        scale=args.scale,
)
    print('Pipeline complete. Summary:')
    print(json.dumps(metadata, indent=2))

if __name__ == '__main__':
    main()
