"""
Setup configuration for Crime Detector System - ML Module
Handles installation and distribution of the ML pipeline package
"""

from setuptools import setup, find_packages
import os

# Read the requirements from requirements.txt
def read_requirements(filename="requirements.txt"):
    """Read requirements from requirements.txt file"""
    req_path = os.path.join(os.path.dirname(__file__), filename)
    with open(req_path, "r", encoding="utf-8") as f:
        return [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

# Read the README for long description
def read_readme():
    """Read README for package long description"""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Crime Detector System - ML Module"

setup(
    name="crime-detector-ml",
    version="1.0.0",
    description="Machine Learning pipeline for Crime Detector System - AI-powered crime detection and investigation support",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="RICHARD-OBENG",
    author_email="richard@crimedetector.local",
    url="https://github.com/RICHARD-OBENG/Crime-Detector-System",
    license="Proprietary",
    python_requires=">=3.10",
    
    packages=find_packages(where=".", include=["*"]),
    
    install_requires=read_requirements("requirements.txt"),
    
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.7.0",
            "ipython>=8.18.0",
        ],
        "gpu": [
            "torch-cuda>=11.8",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "crime-detector-train=ml.pipelines.training_pipeline:main",
            "crime-detector-infer=ml.pipelines.inference_pipeline:main",
            "crime-detector-validate=ml.validation.model_validation:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    
    keywords=[
        "crime detection",
        "machine learning",
        "deep learning",
        "facial recognition",
        "pattern detection",
        "risk assessment",
        "law enforcement",
        "investigation",
        "tensorflow",
        "pytorch",
        "xgboost",
    ],
    
    project_urls={
        "Documentation": "https://github.com/RICHARD-OBENG/Crime-Detector-System/tree/main/docs",
        "Source": "https://github.com/RICHARD-OBENG/Crime-Detector-System",
        "Issues": "https://github.com/RICHARD-OBENG/Crime-Detector-System/issues",
    },
    
    include_package_data=True,
    zip_safe=False,
)
