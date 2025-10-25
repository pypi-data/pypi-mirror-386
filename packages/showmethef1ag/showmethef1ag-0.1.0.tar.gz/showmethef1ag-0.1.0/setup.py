from setuptools import setup, find_packages

setup(
    name="showmethef1ag",
    version="0.1.0",
    description="A package that prints /flag (for local testing only)",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "showmethef1ag=showmethef1ag.test:main"
        ]
    },
    python_requires=">=3.8",
)