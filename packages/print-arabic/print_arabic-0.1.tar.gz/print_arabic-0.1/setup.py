from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="print-arabic",
    version="0.1",
    author="Azwri",
    author_email="aazwri@gmail.com",
    description="A Python library to print Arabic text with proper bidirectional support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/azwri/print_arabic",
    py_modules=["print_arabic"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.6",
    install_requires=[
        "python-bidi>=0.4.2",
        "arabic-reshaper>=2.1.3",
    ],
    keywords="arabic print display bidi bidirectional reshaper text",
)
