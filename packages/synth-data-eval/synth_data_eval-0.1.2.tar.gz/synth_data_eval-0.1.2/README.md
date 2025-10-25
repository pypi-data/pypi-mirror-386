# synth-data-eval repo

[![CI](https://github.com/ahmed-fouad-lagha/synth-data-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmed-fouad-lagha/synth-data-eval/actions/workflows/ci.yml)
[![Code Quality](https://github.com/ahmed-fouad-lagha/synth-data-eval/actions/workflows/code-quality.yml/badge.svg)](https://github.com/ahmed-fouad-lagha/synth-data-eval/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/ahmed-fouad-lagha/synth-data-eval/branch/main/graph/badge.svg)](https://codecov.io/gh/ahmed-fouad-lagha/synth-data-eval)
[![PyPI version](https://badge.fury.io/py/synth-data-eval.svg)](https://pypi.org/project/synth-data-eval/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A collaborative research project investigating methods for generating and evaluating synthetic tabular data across multiple domains.
This repository contains reproducible code, datasets, and experiment configurations used in our paper preparation.

---

## 📚 Project Overview

Synthetic data is crucial for privacy-preserving machine learning.
This project evaluates different synthetic data generators (CTGAN, TVAE, Gaussian Copula) across statistical fidelity, ML utility, privacy, and data quality.

**Research Objective:**
To provide a systematic benchmark framework and identify trade-offs between realism, privacy, and downstream task performance.

---

## 🚀 Installation

### From PyPI (Recommended)
```bash
pip install synth-data-eval
```

### From Source (Development)
```bash
git clone https://github.com/ahmed-fouad-lagha/synth-data-eval.git
cd synth-data-eval
pip install -e ".[all]"  # Install with all optional dependencies
```

### Optional Dependencies
```bash
pip install -e ".[dev]"      # Development tools (pytest, mypy, black, etc.)
pip install -e ".[docs]"     # Documentation building
pip install -e ".[notebooks]" # Jupyter notebook support
```

---

## 🧵 Repository Structure
```
synthetic-tabular-eval/
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore
├── generators/
│   ├── __init__.py
│   ├── base_generator.py
│   ├── ctgan_model.py
│   ├── tvae_model.py
│   └── gaussian_copula.py
├── evaluation/
│   ├── __init__.py
│   ├── sdmetrics_evaluation.py
│   ├── ml_utility.py
│   └── privacy_metrics.py
├── scripts/
│   ├── config.yaml
│   ├── run_benchmark.py
│   ├── visualize_results.py
│   └── download_datasets.py
├── tests/
│   ├── __init__.py
│   ├── test_generators.py
│   └── test_evaluation.py
├── datasets/
├── results/
└── logs/
```

---

## 🔬 Experimental Setup

### Datasets
We evaluated on two benchmark datasets:
- **Adult Income**: 32,048 training samples, 14 features (8 categorical, 6 numerical)
- **Diabetes**: 353 training samples, 10 numerical features

### Generators
- **CTGAN**: GAN-based with mode-specific normalization for categorical data
- **TVAE**: Variational autoencoder approach optimized for tabular data
- **Gaussian Copula**: Parametric baseline using copula-based modeling

### Evaluation Metrics
- **Statistical Fidelity**: Correlation similarity, Kolmogorov-Smirnov complement
- **ML Utility**: Train-on-Synthetic-Test-on-Real (TSTR) paradigm with utility ratios
- **Privacy**: Distance to Closest Record (DCR), Nearest Neighbor Distance Ratio (NNDR)

### Implementation Details
- **5 independent runs** per configuration for statistical robustness
- **300 epochs** for deep learning models (CTGAN, TVAE)
- **Python 3.10**, **SDV 1.28**, **CTGAN 0.7**
- **Statistical significance testing** with t-tests and confidence intervals

---

## 📊 Key Findings

**Performance Highlights:**
- **TVAE excels on classification tasks** (Adult Income: 0.908 ± 0.028 utility ratio)
- **Gaussian Copula dominates regression tasks** (Diabetes: 0.964 ± 0.000 utility ratio)
- **Massive training time differences**: CTGAN (1022s) vs Gaussian Copula (4.9s) = 200x efficiency gap
- **8 statistically significant differences** detected across metrics and datasets

**Trade-offs Identified:**
- GAN-based generators (CTGAN, TVAE) show negative utility on small regression datasets
- Gaussian Copula provides best privacy-utility balance, especially for smaller datasets
- Dataset size significantly impacts generator performance and optimal choice

---

## 🧬 Experiment Pipeline

**Completed Research Workflow:**
- **Data Preparation:** Adult Income (32K samples) and Diabetes (353 samples) datasets
- **Generation:** 5 independent runs each of CTGAN (300 epochs), TVAE (300 epochs), Gaussian Copula
- **Evaluation:** Statistical fidelity (SDMetrics), ML utility (TSTR paradigm), privacy metrics (DCR, NNDR)
- **Analysis:** Statistical significance testing, confidence intervals, comprehensive visualizations

**Key Scripts:**
- `scripts/run_benchmark.py` - Execute complete experimental pipeline
- `scripts/statistical_analysis.py` - Generate significance tests and LaTeX tables
- `scripts/visualize_results.py` - Create radar plots, heatmaps, and utility comparisons
- `paper/main.tex` - Complete research paper with results and analysis

---

## 🔄 Reproducing Results

```bash
# 1. Install dependencies
pip install -e ".[all]"

# 2. Download datasets
python scripts/download_datasets.py

# 3. Run complete benchmark (will take several hours)
python scripts/run_benchmark.py

# 4. Generate statistical analysis
python scripts/statistical_analysis.py

# 5. Create visualizations
python scripts/visualize_results.py

# 6. Compile paper
cd paper && pdflatex main.tex
```

**Expected Runtime:** ~2-3 hours for full experimental pipeline with 5 runs × 3 generators × 2 datasets.

---

## �️ Development

### Prerequisites
- Python 3.8+
- pip

### Setup
```bash
# Clone the repository
git clone https://github.com/ahmed-fouad-lagha/synth-data-eval.git
cd synth-data-eval

# Install in development mode with all dependencies
pip install -e ".[dev,docs,notebooks]"

# Optional: Install pre-commit hooks for code quality
pip install pre-commit
pre-commit install
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=generators --cov=evaluation

# Run specific test file
pytest tests/test_generators.py
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type check
mypy generators/ evaluation/ scripts/
```

### Documentation
```bash
# Build documentation
cd docs
sphinx-build -b html . _build/html

# View documentation
open _build/html/index.html
```

### CI/CD
This project uses GitHub Actions for continuous integration:

- **CI Pipeline**: Runs on every push/PR with testing, linting, documentation building, and security scanning
- **Multi-Python Support**: Tests on Python 3.8, 3.9, 3.10, and 3.11
- **Code Quality**: Automated checks for formatting, linting, and type safety
- **Coverage**: Code coverage reporting with Codecov integration
- **Security**: Automated vulnerability scanning
- **Release**: Automated PyPI publishing on version tags

---

## 📦 Creating Releases

### Automated Release Process
Use the provided release script for consistent versioning and publishing:

```bash
# Patch release (0.1.0 -> 0.1.1)
python scripts/make_release.py patch

# Minor release (0.1.0 -> 0.2.0)
python scripts/make_release.py minor

# Major release (0.1.0 -> 1.0.0)
python scripts/make_release.py major

# Specific version release
python scripts/make_release.py v1.0.0
```

The script will:
- ✅ Run all quality checks (tests, linting, type checking)
- ✅ Update version in `pyproject.toml`
- ✅ Update `CHANGELOG.md` with release date
- ✅ Build and validate the package
- ✅ Create a git tag and push to trigger PyPI publishing

### Manual Release Process
If you prefer manual control:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes: `git commit -m "Release v1.0.0"`
4. Create tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
5. Push: `git push origin v1.0.0`
6. GitHub Actions will automatically publish to PyPI

### Testing Releases
You can test releases on TestPyPI before publishing to production:

1. Go to GitHub Actions → Release workflow
2. Click "Run workflow"
3. Select "testpypi" target
4. Install from TestPyPI: `pip install --index-url https://test.pypi.org/simple/ synth-data-eval`

### Private Repository Setup
If your repository is private, GitHub release creation requires a Personal Access Token (PAT):

1. **Create a Personal Access Token (PAT)**:
   - Go to https://github.com/settings/tokens
   - Generate a new token with `repo` scope
   - Copy the token

2. **Add to Repository Secrets**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add a new secret named `RELEASE_TOKEN`
   - Paste your PAT as the value

3. **✅ Status**: RELEASE_TOKEN is now configured - GitHub releases will work automatically!

---

## �🔒 Repository Policy

- This repository is **private**, accessible only to core authors.
- Do not upload confidential or non-public datasets.
- Results and scripts shared here are for pre-publication collaboration only.

---

## 📄 License
Internal Research Use Only (non-distributable until publication).
For publication release, this will switch to MIT license.
