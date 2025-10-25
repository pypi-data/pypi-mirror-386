"""
Setup configuration for PyNearshore package

Modern Python package for nearshore wave propagation and sediment transport modeling.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "PyNearshore - Nearshore wave propagation and sediment transport modeling"

setup(
    name="pynearshore",
    version="2.0.0",
    author="Pavlishenku",
    author_email="pavlishenku@gmail.com",
    description="Nearshore wave propagation, currents, and sediment transport modeling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pavlishenku/pynearshore",
    project_urls={
        "Bug Reports": "https://github.com/pavlishenku/pynearshore/issues",
        "Source": "https://github.com/pavlishenku/pynearshore",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Hydrology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    keywords=[
        "coastal engineering",
        "wave propagation",
        "sediment transport",
        "nearshore dynamics",
        "wave breaking",
        "Goda model",
        "Battjes-Janssen",
        "Bailard model",
        "numerical methods",
        "Runge-Kutta",
        "oceanography",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
        "scipy>=1.5.0",
    ],
    extras_require={
        "viz": [
            "matplotlib>=3.0.0",
            "seaborn>=0.11.0",
        ],
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.900",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
