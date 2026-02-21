from setuptools import setup, find_packages

setup(
    name="maisb_runner",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
        "matplotlib>=3.6.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "maisb=maisb_runner.cli:main",
        ]
    },
)
