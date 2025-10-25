from setuptools import setup, find_packages
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def parse_requirements():
    requirements_file = BASE_DIR / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="logflow_python",
    version="1.0.2",
    packages=find_packages(),
    install_requires=parse_requirements(),
    author="Aleko Khomasuridze",
    author_email="aleko.khomasurize@gmail.com",
    description="A simple but modular logging library for Python applications.",
    long_description=(BASE_DIR / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/aleko-khomasuridze/LogFlow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
