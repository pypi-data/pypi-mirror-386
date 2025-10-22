# CBSL Rice Price Collector

![PyPI](https://img.shields.io/pypi/v/cbsl_rice_price_collector?color=blue)
![Build](https://github.com/ChamoChiran/rice_price_collector/actions/workflows/publish-to-pypi.yml/badge.svg)
<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

cbsl_rice_price_collector collects rice prices from the CBSL website and provides tools for downloading, parsing, and processing rice price data.

---

## Installation

Install from PyPI:

```bash
pip install cbsl_rice_price_collector
```

Or install from source:

```bash
git clone https://github.com/ChamoChiran/rice_price_collector.git
cd rice_price_collector
pip install .
```

## Usage

Download rice price PDFs and process them:

```python
from rice_price_collector.downloader import pdf_downloader
from rice_price_collector.parser import parser

# Download PDFs
data_dir = "./data/raw/2024"
pdf_downloader.download_pdfs(data_dir)

# Parse PDFs
parsed_data = parser.parse_pdfs(data_dir)
```

See the [docs](docs/README.md) for more details and advanced usage.

---

## Project Organization

```
├── LICENSE
├── Makefile
├── README.md
├── data/
│   ├── processed/
│   └── raw/
├── docs/
├── models/
├── notebooks/
├── pyproject.toml
├── references/
├── reports/
│   └── figures/
├── requirements.txt
├── rice_price_collector/
│   ├── __init__.py
│   ├── config.py
│   ├── downloader/
│   └── parser/
└── tests/
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests for improvements or bug fixes.

## License

This project is licensed under the terms of the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, open an issue or contact [ChamoChiran](https://github.com/ChamoChiran).
