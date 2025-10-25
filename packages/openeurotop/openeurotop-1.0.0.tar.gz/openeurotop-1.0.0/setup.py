from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openeurotop",
    version="1.0.0",
    author="OpenEurOtop Contributors",
    author_email="pavlishenku@gmail.com",
    description="Implémentation Python du guide EurOtop pour le calcul du franchissement de vagues",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pavlishenku/OpenEurOtop",
    project_urls={
        "Bug Tracker": "https://github.com/Pavlishenku/OpenEurOtop/issues",
        "Documentation": "https://openeurotop.readthedocs.io/",
        "Source Code": "https://github.com/Pavlishenku/OpenEurOtop",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs", "scripts"]),
    package_data={
        "openeurotop": ["data/*.pkl", "data/*.json", "data/*.txt"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Hydrology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="eurotop wave overtopping coastal engineering hydraulics",
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
            "xgboost>=1.5.0",
            "tensorflow>=2.8.0",
        ],
        "all": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "scikit-learn>=1.0.0",
            "xgboost>=1.5.0",
            "tensorflow>=2.8.0",
        ],
    },
)
