from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="zeska-lang",
    version="0.4.0",  # 🚀 Updated version
    author="Sibi",
    author_email="Smartsibi65hacker@example.com",
    description="Tanglish-based beginner-friendly programming language that auto-corrects, speaks (sayu), and self-heals.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pyttsx3"
    ],
    entry_points={
        "console_scripts": [
            "zeska=zeska:main"
        ]
    },
    python_requires=">=3.7",
    license="MIT",
    url="https://github.com/Smartsibi65hacker/ZeskaLang",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Education",
        "Topic :: Software Development :: Interpreters",
    ],
)
