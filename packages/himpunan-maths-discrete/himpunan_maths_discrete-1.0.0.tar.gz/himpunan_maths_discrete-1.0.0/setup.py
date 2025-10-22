from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="himpunan-maths-discrete",
    version="1.0.0",
    author="Wyatt Matthew",
    author_email="wyatt.honny06@gmail.com",
    description="Implementasi teori himpunan untuk Matematika Diskrit dalam Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wyattmatt/himpunan-maths-discrete",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="matematika diskrit himpunan set theory discrete mathematics",
    python_requires=">=3.7",
    project_urls={
        "Bug Reports": "https://github.com/wyattmatt/himpunan-maths-discrete/issues",
        "Source": "https://github.com/wyattmatt/himpunan-maths-discrete",
    },
)