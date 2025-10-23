from setuptools import setup, find_packages

setup(
    name="zeska",
    version="0.1.0",
    packages=find_packages(),
    py_modules=['zeska'],
    entry_points={
        "console_scripts": [
            "zeska=zeska:main"
        ]
    },
)
