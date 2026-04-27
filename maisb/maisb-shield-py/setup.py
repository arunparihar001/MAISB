# setup.py
# Save at the ROOT of the maisb_shield folder (one level ABOVE maisb_shield/)
#
# Folder structure must look like:
#   maisb-shield-py/
#   ├── setup.py            ← this file
#   └── maisb_shield/
#       ├── __init__.py
#       └── shield.py
#
# HOW TO BUILD AND PUBLISH:
#   pip install build twine
#   python -m build
#   python -m twine upload dist/*

from setuptools import setup, find_packages

setup(
    name="maisb-shield",
    version="1.0.0",
    description="MAISB Shield SDK — prompt injection protection for mobile AI agents",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="MAISB",
    author_email="your@email.com",          # ← replace with your email
    url="https://github.com/your-org/maisb-benchmark",  # ← replace
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
