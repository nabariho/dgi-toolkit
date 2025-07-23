# dgi-toolkit

[![Build Status](https://img.shields.io/github/actions/workflow/status/nabariho/dgi-toolkit/pr.yml?branch=main)](https://github.com/nabariho/dgi-toolkit/actions)
[![Coverage](https://img.shields.io/codecov/c/github/nabariho/dgi-toolkit/main)](https://codecov.io/gh/nabariho/dgi-toolkit)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Image size](https://img.shields.io/docker/image-size/nabariho/dgi-toolkit/latest)](https://hub.docker.com/r/nabariho/dgi-toolkit)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nabariho/dgi-toolkit/main?filepath=notebooks%2Fdgi_portfolio_builder.ipynb)

## Project Pitch

**dgi-toolkit** is a Python toolkit for building, analyzing, and managing Dividend Growth Investing portfolios. It aims to provide robust, extensible tools for research, automation, and reporting for DGI investors.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/nabariho/dgi-toolkit.git
cd dgi-toolkit

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run the CLI screener (example)
poetry run dgi screen --min-yield 0.03
```

## Example CLI Output

```
  DGI Screen Results
  ┏━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┳━━━━━━━┓
  ┃Symbol┃Name              ┃Yield ┃Payout  ┃CAGR ┃FCF Yield ┃Score ┃
  ┡━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━╇━━━━━━━━━━━╇━━━━━━━┩
  ┃AAPL  ┃Apple Inc.        ┃0.60  ┃15.00   ┃8.50 ┃5.20      ┃0.178 ┃
  ┃MSFT  ┃Microsoft Corp.   ┃0.80  ┃35.00   ┃10.0 ┃7.00      ┃0.253 ┃
  ┃GOOG  ┃Alphabet Inc.     ┃0.70  ┃25.00   ┃12.0 ┃6.50      ┃0.276 ┃
  ┃JNJ   ┃Johnson & Johnson ┃2.50  ┃50.00   ┃6.00 ┃4.00      ┃0.120 ┃
  ┃PG    ┃Procter & Gamble  ┃1.20  ┃55.00   ┃5.50 ┃3.80      ┃0.089 ┃
  └───────┴──────────────────┴───────┴────────┴──────┴───────────┴───────┘
```

## Notebook Demo

You can try the full pipeline in your browser (no install needed):

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nabariho/dgi-toolkit/main?filepath=notebooks%2Fdgi_portfolio_builder.ipynb)

---

## License
MIT
