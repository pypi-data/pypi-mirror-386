"""Grid utilities used by pipeline."""
import numpy as np

def init_grid(size, seed=12345):
    np.random.seed(seed)
    return np.ones((size,size,3), dtype=np.uint8)*255
