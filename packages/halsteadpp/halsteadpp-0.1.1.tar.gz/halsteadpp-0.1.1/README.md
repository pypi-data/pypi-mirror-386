# Halstead++

A sophisticated Python library for analyzing Halstead complexity metrics of C code through AST parsing, with intelligent operator filtering for more accurate complexity assessment.
Introduction

Halstead++ is a specialized static analysis tool that calculates Halstead complexity metrics for C programming language code. Unlike traditional Halstead metric tools, Halstead++ employs intelligent filtering to exclude common syntactic operators that tend to artificially inflate complexity scores, such as semicolons, parentheses, braces, and commas. This results in more accurate and meaningful complexity measurements that better reflect the actual cognitive complexity of the code.

The tool leverages pycparser to generate Abstract Syntax Trees (AST) from preprocessed C code and performs comprehensive analysis at both file and function levels, providing detailed metrics including program vocabulary, volume, difficulty, effort, and estimated bug counts.

# Installation

### From PyPI
```
pip install halsteadpp
```

### From Source
```
git clone https://github.com/Morgadineo/Halsteadpp
cd halsteadpp
pip install -e .
```

## Dependencies
Python >= 3.8

pycparser >= 2.21

rich >= 13.0 (for formatted output)

# Usage
## Prerequisites: Code Preprocessing

Before using Halstead++, C source files must be preprocessed using the provided Makefile. This step is necessary because Halstead++ uses pycparser which requires preprocessed C code.
Using the Makefile

The repository includes a Makefile for easy preprocessing:
```
# Preprocess all .c files in the Examples directory
make DIR=Examples

# Or use the default directory
make
```

## Basic Usage
```
from halsteadpp import ParsedCode

# Analyze a C file (without .c extension)
parser = ParsedCode("example_file", "path/to/preprocessed/code/")

# Display comprehensive complexity metrics
parser.print_complexities()

# Display function-level analysis
parser.print_functions()
```

## Advanced Usage
```
from halsteadpp import ParsedCode

# Initialize parser for specific file
parser = ParsedCode(
    filename="algorithm",      # File name without extension
    file_dir="src/complex/"    # Directory containing preprocessed .i file
)

# Access metrics directly
print(f"Program Volume: {parser.volume}")
print(f"Estimated Bugs: {parser.delivered_bugs}")
print(f"Cyclomatic Complexity: {parser.total_mcc}")

# Access function-specific metrics
for function in parser.functions:
    print(f"Function: {function.func_name}")
    print(f"  - Halstead Effort: {function.effort}")
    print(f"  - McCabe Complexity: {function.total_mcc}")
```

## Example 1: Simple Analysis

**hello.c inside 'Example/' folder:**
```
#include <stdio.h>

int main(void)
{
  printf("Hello, World!\n");
  
  return 0;
}
```

**Pre-compile:**
```
> make

Preprocessing Examples/hello.c...
```

**Basic main.py:**
```
from halsteadpp import ParsedCode

# Analyze a C file
hello_code = ParsedCode('hello', 'Examples/')

# Print table of complexities
hello_code.print_complexities()
```

### Outputs
#### Complexities Table
<img width="300" height="400" alt="Captura de tela de 2025-10-19 15-09-59" src="https://github.com/user-attachments/assets/13ebc988-6d05-431b-8c1b-187ffb7bba88" />


#### Functions complexity
<img width="1600" height="121" alt="Captura de tela de 2025-10-19 15-11-01" src="https://github.com/user-attachments/assets/67d64d06-00fa-4dc2-a50f-7a27729e8747" />

#### Operators
<img width="350" height="130" alt="Captura de tela de 2025-10-19 15-11-45" src="https://github.com/user-attachments/assets/d5a53b61-a27d-427e-86d7-6003b519daea" />

#### Operands
<img width="350" height="130" alt="Captura de tela de 2025-10-19 15-12-13" src="https://github.com/user-attachments/assets/4bdfe440-3ac2-4b48-9105-79f389e9136a" />


# Key Features

## Intelligent Operator Filtering

Halstead++ excludes the following syntactic operators from complexity calculations:

Semicolons (;)

Parentheses (())

Braces ({})

Commas (,)

This filtering provides more realistic complexity metrics by focusing on meaningful operators that contribute to actual cognitive load.

## Comprehensive Metrics

Halstead Metrics: n1, n2, N1, N2, vocabulary, length, volume, difficulty, level, effort, time, bugs

Cyclomatic Complexity: McCabe complexity at function and file levels

Line Metrics: Total lines, effective lines (excluding comments and empty lines)

Function Analysis: Individual metrics for each function

## Rich Visual Output

Formatted tables using the Rich library

Color-coded output for better readability

Detailed operator and operand listings

## AST-Based Analysis

Accurate parsing using Python's AST capabilities

Support for complex C constructs (pointers, structs, function calls, etc.)

Real node detection to filter out compiler-generated code

## Metric Definitions
n1: Number of distinct operators

n2: Number of distinct operands

N1: Total number of operators

N2: Total number of operands

Volume (V): Program size metric: (N1 + N2) × log₂(n1 + n2)

Difficulty (D): Program complexity: (n1 / 2) × (N2 / n2)

Effort (E): Mental effort required: D × V

Bugs (B): Estimated number of delivered bugs: E^(2/3) / 3000

# License

MIT License - see LICENSE file for details.

