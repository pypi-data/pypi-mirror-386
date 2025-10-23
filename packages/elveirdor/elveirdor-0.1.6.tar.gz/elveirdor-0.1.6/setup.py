from setuptools import setup, find_packages

setup(
    name="elveirdor",
    version="0.1.6",
    author="Elveirdor Systems",
    description="Elveirdor Infinity Computing Pipeline with visual generation, decoding, and export features.",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pillow",
        "matplotlib",
    ],
    entry_points={
        "console_scripts": [
            "elveirdor=elveirdor.cli:main",
        ],
    },
    python_requires=">=3.8",
)
