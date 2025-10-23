"""Simple Elveirdor computing engine (expandable)."""

from ..pipeline import run_elveirdor_pipeline

class ElveirdorEngine:
    def __init__(self, grid_size=20, seed=12345):
        self.grid_size = grid_size
        self.seed = seed

    def run(self, text="ELVEIRDOR", sequence=None, output="output.png"):
        """Run pipeline and return output filename."""
        run_elveirdor_pipeline(grid_size=self.grid_size, output_filename=output, text=text, sequence=sequence)
        return output
