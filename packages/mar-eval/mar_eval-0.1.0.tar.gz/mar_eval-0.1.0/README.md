# mar-eval
![CI](https://github.com/cdc15000/mar-eval/actions/workflows/tests.yml/badge.svg)

A Python toolkit for evaluating **Metal Artifact Reduction (MAR)** performance in CT imaging.

---

## Overview

**mar-eval** provides a reproducible framework for evaluating MAR performance using objective, task-based metrics.  
It supports both **digital** and **quantitative physical** test methods consistent with the procedures described in *IEC 60601-2-44, Annex GG (informative)*.

The toolkit implements:

- **Channelized Hotelling Observer (CHO)** analysis for lesion-detection tasks  
- **AUC computation** as the figure of merit for detectability  
- **Bias and statistical comparison** modules for ΔAUC analysis  
- Modular support for simulated (digital) and scanned (physical) image datasets  
- A transparent and open-source foundation for regulatory and manufacturer use

---

## Installation

### Option 1 – Install directly from GitHub

```bash
pip install git+https://github.com/cdc15000/mar-eval.git
```

### Option 2 – Clone and install locally

```bash
git clone https://github.com/cdc15000/mar-eval.git
cd mar-eval
pip install .
```

---

## Example Usage

```python
from mareval.cho import compute_cho
from mareval.stats import compute_auc

# Example: run CHO analysis on lesion-present and lesion-absent image sets
auc = compute_auc(lesion_present, lesion_absent)
print(f"AUC = {auc:.3f}")
```

For a complete demonstration, see the example script:  
[`examples/synthetic_demo.py`](examples/synthetic_demo.py)

---

## Features

| Category | Description |
|-----------|--------------|
| **CHO Analysis** | Implements a channelized Hotelling observer for model-based detectability tasks |
| **AUC Metrics** | Computes area under the ROC curve for lesion-detection performance |
| **Bias Assessment** | Quantifies ΔAUC between MAR-enabled and non-MAR reconstructions |
| **Statistical Comparison** | Supports one-tailed paired *t*-tests or nonparametric equivalents |
| **Extensibility** | Designed for integration with validated simulators and test devices |

---

## Contributing

Contributions are welcome.  
If you identify issues, propose improvements, or want to extend the toolkit, please open an [Issue](https://github.com/cdc15000/mar-eval/issues) or submit a [Pull Request](https://github.com/cdc15000/mar-eval/pulls).

---

## Citation

If you use this toolkit in academic or regulatory work, please cite:

> Cocchiaraley, C.D., *mar-eval: A Python Toolkit for Objective Evaluation of Metal Artifact Reduction in CT Imaging* (2025).  
> Available at: [https://github.com/cdc15000/mar-eval](https://github.com/cdc15000/mar-eval)

---

## License

This project is licensed under the MIT License.  
See [LICENSE](LICENSE) for details.

---

## Acknowledgment

Development of this toolkit is informed by ongoing work within **IEC TC 62 / SC 62B WG 30** and related DICOM initiatives on Metal Artifact Reduction (MAR) in CT imaging.
