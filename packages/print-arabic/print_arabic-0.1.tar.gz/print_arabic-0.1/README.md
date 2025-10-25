# Print Arabic

[![Twitter Follow](https://img.shields.io/twitter/follow/Al_Azwari?label=Follow&style=social)](https://twitter.com/Al_Azwari)
[![Downloads](https://pepy.tech/badge/print-arabic)](https://pepy.tech/project/print-arabic)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/print-arabic?style=plastic)](https://badge.fury.io/py/print-arabic)
[![PyPI version](https://badge.fury.io/py/print-arabic.svg)](https://badge.fury.io/py/print-arabic)

A Python library to print Arabic text with proper bidirectional support in terminals and consoles.

## Overview

`print-arabic` is a simple yet powerful utility that handles the complexity of displaying Arabic text correctly in Python applications. It combines Arabic text reshaping and bidirectional text rendering to ensure Arabic characters are displayed properly.

## Features

- Automatic Arabic text reshaping
- Bidirectional text support
- Simple, easy-to-use API
- Works in terminals and consoles

## Installation

Install using pip:

```bash
pip install print-arabic
```

## Usage

```python
import print_arabic

# Print Arabic text - direct usage
print_arabic("مرحبا بالعالم")

# Print mixed Arabic and English text
print_arabic("Hello مرحبا")

# Print Arabic with numbers
print_arabic("العدد ١٢٣٤٥")

# Alternative: use the function explicitly
print_arabic.print_arabic("النص العربي")
```

## How It Works

The library uses two key components:

1. **arabic-reshaper**: Reshapes Arabic text to connect letters properly
2. **python-bidi**: Applies the bidirectional algorithm for correct text direction

## Requirements

- Python 3.6 or higher
- python-bidi >= 0.4.2
- arabic-reshaper >= 2.1.3

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Azwri (aazwri@gmail.com)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Repository

https://github.com/azwri/print_arabic
