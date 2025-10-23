# Predipy

ML lib Python + Go.

## Setup
1. Go: cd go_backend && go mod tidy && go build -o main main.go
2. Python: pip install -e .

## Run Example
python examples/example_regression.py

## Test
pytest tests/

# Predipy

**Predipy** is a lightweight Python ML library with a Go backend for fast regression and KNN classification.  
It supports linear regression and K-Nearest Neighbors (KNN) for regression & classification.

---

## Features

- Linear regression with normal equation + optional ridge regularization.
- KNN classification with Euclidean distance.
- Lightweight, fast, and works offline.
- Go backend for computational efficiency.
- Easy Python interface.

---

## Installation

Install from PyPI:

```bash
pip install predipy
