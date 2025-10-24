from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="voss-taren",
    version="1.1.0",
    author="Votre Nom",
    description="Effet Matrix authentique en Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'vosstaren=voss_taren.main:cmatrix',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)