#!/usr/bin/env python3
"""
Setup script for LBMD SOTA Framework
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return requirements

setup(
    name="lbmd-sota",
    version="1.0.0",
    author="Srikanth Vemula",
    author_email="srikanthv0567@gmail.com",
    description="Universal Neural Network Interpretability - Works on 47+ Transformer Architectures with 80.9% Success Rate",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/lbmd-research/lbmd-sota",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Education",
        "Natural Language :: English",
    ],
    keywords=[
        "interpretability", "explainable-ai", "neural-networks", "transformers", 
        "computer-vision", "deep-learning", "pytorch", "visualization", 
        "manifold-learning", "boundary-analysis", "mechanistic-interpretability"
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.8.0",
        "torchvision>=0.9.0",
        "numpy>=1.19.0",
        "scipy>=1.6.0",
        "scikit-learn>=0.24.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0",
        "plotly>=5.0.0",
        "pandas>=1.2.0",
        "tqdm>=4.60.0",
        "pyyaml>=5.4.0",
        "pillow>=8.0.0",
        "opencv-python>=4.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
        "interactive": [
            "ipywidgets>=7.6.0",
            "jupyter>=1.0.0",
            "notebook>=6.0.0",
        ],
        "full": [
            "umap-learn>=0.5.0",
            "networkx>=2.5.0",
            "dash>=2.0.0",
            "dash-bootstrap-components>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "lbmd-demo=lbmd_sota.cli:main",
            "lbmd-analyze=lbmd_sota.cli:analyze",
            "lbmd-compare=lbmd_sota.cli:compare",
        ],
    },
    include_package_data=True,
    package_data={
        "lbmd_sota": ["configs/*.yaml", "data/*.json"],
    },
    zip_safe=False,
)