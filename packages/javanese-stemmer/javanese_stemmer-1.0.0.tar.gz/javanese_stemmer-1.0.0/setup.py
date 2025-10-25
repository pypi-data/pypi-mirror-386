from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="javanese-stemmer",
    version="1.0.0",
    author="Stevia Anlena Putri",  # ⚠️ CHANGE THIS TO YOUR NAME
    author_email="stevia.ap@gmail.com",  # ⚠️ CHANGE THIS TO YOUR EMAIL
    description="A comprehensive Javanese language stemmer with morphophonological rules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/javanese-stemmer",  # Optional
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.0.0",
    ],
    keywords="javanese, stemmer, nlp, natural language processing, indonesian, morphology",
)
