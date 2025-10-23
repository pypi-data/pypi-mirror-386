from setuptools import setup, find_packages

setup(
    name="elveirdor",
    version="0.1.4",
    author="You",
    description="ELVEIRDOR Infinity Computing pipeline",
    packages=find_packages(),
    install_requires=["numpy", "pillow", "matplotlib"],
    entry_points={"console_scripts": ["elveirdor=elveirdor.cli:main"]},
    python_requires=">=3.8",
)
