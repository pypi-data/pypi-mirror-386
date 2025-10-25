![PyPI version](https://img.shields.io/pypi/v/sync_openweatherapi_python_sdk)
![License](https://img.shields.io/badge/license-MIT-blue)

# Sync OpenWeatherAPI Python SDK 🌦️

A lightweight, synchronous Python SDK for [OpenWeatherMap API](https://openweathermap.org/api).  
Provides clean abstractions for common endpoints like **Current Weather** and **5-Day Forecast**, built with developer ergonomics and testability in mind.

---

### 📚 Table of Contents
- [🚀 Features](#-features)
- [🧩 Installation](#-installation)
- [🔑 Setup](#-setup)
- [🧠 Usage](#-usage)
- [🧪 Testing](#-testing)
- [🏗️ Project structure](#-project-structure)
- [🧰 Development shortcuts](#-development-shortcuts)
- [🪶 License](#-license)
- [🌍 Roadmap](#-roadmap)

---

## 🚀 Features
- **Sync client** using `requests` with connection pooling and retries  
- Built-in error handling (`AuthenticationError`, `RateLimitError`, etc.)  
- Optional **Pydantic models** for typed responses  
- `.env` support via `python-dotenv`  
- 100 % offline test suite with `pytest` + `responses`  
- Type-checked (`mypy`) & linted (`ruff`)

---

## 🧩 Installation

### From source (recommended for development)
```bash
git clone https://github.com/nkpythondeveloper/sync_openweatherapi_python_sdk.git
cd sync_openweatherapi_python_sdk
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

---

## 🔑 Setup
Create a `.env` file in the project root:
```bash
OPENWEATHER_KEY=your_real_api_key_here
```
> Never commit your `.env` — it’s already ignored in `.gitignore`.

---

## 🧠 Usage

### Basic example
```python
from openweather import OpenWeatherClient

client = OpenWeatherClient(api_key="YOUR_KEY")
data = client.get_current_weather(city="Pune")
print(f"{data['name']}: {data['main']['temp']}°C, {data['weather'][0]['description']}")
```

### With `.env` auto-load
```python
import os
from dotenv import load_dotenv
from openweather import OpenWeatherClient

load_dotenv()
client = OpenWeatherClient(api_key=os.getenv("OPENWEATHER_KEY"))

forecast = client.get_forecast(city="Pune")
print(forecast['city']['name'], len(forecast['list']))
```

---

## 🧪 Testing
Run all tests offline:
```bash
pytest -q
```
Check lint & types:
```bash
ruff check .
mypy openweather
```

---

## 🏗️ Project structure
```
sync_openweatherapi_python_sdk/
├── openweather/
│   ├── __init__.py
│   ├── client.py
│   ├── endpoints.py
│   ├── exceptions.py
│   ├── models.py
│   └── utils.py
├── examples/
│   └── usage_sync.py
├── tests/
│   └── test_client_sync.py
├── pyproject.toml
└── README.md
```

---

## 🧰 Development shortcuts
| Command | Purpose |
|----------|----------|
| `pytest -q` | run tests |
| `ruff check .` | lint code |
| `mypy openweather` | type-check |
| `python -m examples.usage_sync` | manual run |

---

## 🪶 License
MIT License © 2025 [Nitin S. Kulkarni]

---

## 🌍 Roadmap
- [ ] Async client (`httpx`)  
- [ ] One Call API  
- [ ] CLI entrypoint (`ow current --city Pune`)  
- [ ] GitHub Actions CI pipeline
