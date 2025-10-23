# tabular-column-classifier

Classify tabular columns with spaCy’s fast model, optionally assisted by an LLM. The library keeps a predictable output format so you can plug it straight into data-quality pipelines or catalog tooling.

## Features

- Uses the lightweight `en_core_web_sm` spaCy model for fast entity detection on column samples.
- Optional LLM refinement layer with configurable host, headers, and model (tested with Ollama).
- Works with single columns or batches of DataFrames and keeps the output `{classification, probabilities}` contract.
- Word-count safeguard avoids labelling free-text columns as entities.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install tabular-column-classifier
python -m spacy download en_core_web_sm
```

Optional extras for LLM support inside the same virtual environment:

```bash
python -m pip install tabular-column-classifier[llm]
```

Working from a local checkout (before the project is on PyPI)? Install with:

```bash
python -m pip install ".[llm]"  # quotes required on zsh
```

> **Tip:** Using `python -m pip` ensures the package installs into the interpreter of your active virtual environment.

## Quick start

```python
import pandas as pd
from column_classifier import ColumnClassifier

movies = pd.DataFrame(
    {
        "title": ["Inception", "The Matrix", "Interstellar"],
        "director": ["Christopher Nolan", "The Wachowskis", "Christopher Nolan"],
        "release_year": [2010, 1999, 2014],
    }
)

companies = pd.DataFrame(
    {
        "company": ["Google", "Microsoft", "Apple"],
        "hq": ["California", "Washington", "California"],
        "founded": [1998, 1975, 1976],
    }
)

classifier = ColumnClassifier(sample_size=25)
table_result = classifier.classify_table(movies, table_name="movies")
print(table_result["columns"]["director"]["classification"])
# PERSON

more_results = classifier.classify_multiple_tables([movies, companies])
print(more_results[1]["columns"]["founded"]["classification"])
# NUMBER
```

### Optional LLM refinement

Add an LLM to overrule spaCy when it is confident enough. The host and headers are passed down to `ollama.Client`, so you can point to a gateway that requires authentication.

```python
from column_classifier import ColumnClassifier

llm_config = {
    "enabled": True,
    "model": "gemma3",
    "host": "https://ollama.your-company.com",
    "headers": {"Authorization": "Basic QWxhZGRpbjpPcGVuU2VzYW1l"},  # Basic <base64>
    "max_samples": 8,  # optional: limit rows sent to the LLM
    "max_retries": 2,  # optional: retry if the model ignores the JSON contract
    "retry_delay": 0.5,  # seconds to wait between retries
}

classifier = ColumnClassifier(llm_config=llm_config, llm_weight=0.7)
table_result = classifier.classify_table(movies, table_name="movies")
print(table_result["columns"]["director"])
```

```python
{'classification': 'PERSON',
 'probabilities': {'PERSON': 0.67, 'STRING': 0.33},
 'sources': {
     'spacy': {'probabilities': {'PERSON': 0.67, 'STRING': 0.33},
               'avg_word_count': 2.0},
     'llm': {'source': 'llm',
             'classification': 'PERSON',
             'probabilities': {'PERSON': 0.67, 'STRING': 0.33},
             'attempt': 1}
 }}
```

## API highlights

- `ColumnClassifier(sample_size=50, classification_threshold=0.5, word_threshold=10, llm_config=None, llm_weight=0.5)`
- `classify_column(column_data: pd.Series, column_name: str = "column") -> dict`
- `classify_table(table: pd.DataFrame, table_name: str = "table") -> dict`
- `classify_multiple_tables(tables: list[pd.DataFrame]) -> list[dict]`

### Output schema

Every classified column yields:

```json
{
  "classification": "PERSON",
  "probabilities": {"PERSON": 0.82, "STRING": 0.18},
  "sources": {
    "spacy": {
      "probabilities": {"PERSON": 0.82, "STRING": 0.18},
      "avg_word_count": 2.0
    },
    "llm": {
      "source": "llm|heuristic|fallback",
      "classification": "PERSON",
      "probabilities": {"PERSON": 0.9},
      "attempt": 1
    }
  }
}
```

> **Tip:** When targeting gateways that require HTTP basic authentication, encode your `username:password` pair with Base64 and pass it verbatim via `headers={"Authorization": "Basic <encoded>"}`. The headers dictionary is forwarded unchanged to `ollama.Client`.

If the LLM returns something that cannot be parsed, the classifier will retry with stronger formatting instructions and ultimately fall back to the spaCy-only prediction to keep results deterministic.

## Publishing to PyPI

This project ships with a `setup.py` configured for PyPI. Build and publish with:

```bash
python -m build
twine upload dist/*
```

Remember to bump the version and clean `dist/` between releases.

## License

Apache License 2.0.
