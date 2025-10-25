from setuptools import setup, find_packages

setup(
    name="showflag",
    version="0.1.0",
    description="A package that prints /flag (for local testing only)",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "showflag=showflag.test:main"
        ]
    },
    python_requires=">=3.8",
)