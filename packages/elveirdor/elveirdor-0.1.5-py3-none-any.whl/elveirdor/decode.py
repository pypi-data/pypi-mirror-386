"""Decoding utilities."""

COLOR_KEYS = []  # placeholder, pipeline defines map if needed

def decode_standard(sequence):
    mapping = {i: chr(ord('A')+i-1) for i in range(1,27)}
    return "".join(mapping.get(int(s), '?') for s in sequence.split() if s.isdigit())

def decode_elveirdor(sequence, keys):
    mapping = {i: keys[i-1] for i in range(1, len(keys)+1)}
    return "".join(mapping.get(int(s), '?') for s in sequence.split() if s.isdigit())
