# exchangerateapi-python

A lightweight Python client for exchangerateapi.net providing simple access to two core endpoints.

- Website: [exchangerateapi.net](https://exchangerateapi.net)

## Installation

```bash
pip install exchangerateapi-python
```

## Quick start

```python
from exchangerateapi.client import ExchangeRateApiClient
client = ExchangeRateApiClient(api_key="YOUR_API_KEY")
```

## Usage patterns

- Fetch most recent rates for a base currency, optionally filter symbols.
- Retrieve historical rates for a given date and base currency.

### Latest

```python
from exchangerateapi.client import ExchangeRateApiClient
client = ExchangeRateApiClient(api_key="YOUR_API_KEY")

latest_usd = client.latest(base="USD")
latest_eur_subset = client.latest(base="EUR", symbols=["USD", "GBP", "JPY"])
```

### Historical

```python
from exchangerateapi.client import ExchangeRateApiClient
client = ExchangeRateApiClient(api_key="YOUR_API_KEY")

hist_usd = client.historical(date="2024-01-02", base="USD")
hist_eur_subset = client.historical(date="2024-01-02", base="EUR", symbols=["USD", "GBP", "JPY"])
```

### Run the examples

```bash
EXCHANGERATEAPI_KEY=your_api_key python examples/latest.py
EXCHANGERATEAPI_KEY=your_api_key python examples/historical.py
```

## License

MIT
