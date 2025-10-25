# pydantic-fixturegen: Deterministic Pydantic fixtures for fast, safe tests (pydantic-fixturegen)

> Deterministic Pydantic fixtures and JSON generation via a secure sandboxed CLI and Pluggy plugins.

[![PyPI version](https://img.shields.io/pypi/v/pydantic-fixturegen.svg "PyPI")](https://pypi.org/project/pydantic-fixturegen/)
![Python versions](https://img.shields.io/pypi/pyversions/pydantic-fixturegen.svg "Python 3.10–3.13")
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg "MIT License")

`pydantic-fixturegen` is a **deterministic data generation toolkit for Pydantic v2 models**. It discovers models, builds generation strategies, creates instances, and **emits artifacts**—JSON, **pytest fixtures**, and JSON Schema—through a composable CLI and a **Pluggy** plugin layer.

- **Deterministic seeds** cascade per model/field across Python `random`, **Faker**, and optional **NumPy** RNGs.
- **Safe-import sandbox** executes untrusted model modules with **network lockdown**, **filesystem jail**, and **resource caps**.
- **Emitters** write JSON/JSONL, pytest fixture modules, and schema files with **atomic writes** and reproducibility metadata.
- **Config precedence**: **CLI args** → **`PFG_*` env vars** → **`[tool.pydantic_fixturegen]`** in `pyproject.toml` or YAML → defaults.

---

## Why pydantic-fixturegen (why)

- **Deterministic test data** for reproducible CI.
- **Secure safe-import sandbox** for third-party models.
- **Pluggy-powered data providers** for extension without forks.
- **CLI first**: `pfg list | gen json | gen fixtures | gen schema | gen explain | doctor`.

---

## Features at a glance (features)

| Area           | Highlights                                                                                                                                                                                                                |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Discovery**  | `pfg list` via AST or sandboxed import; include/exclude patterns; public-only; machine-readable errors (`--json-errors`, code `20`).                                                                                      |
| **Generation** | Depth-first builder with recursion/instance budgets; per-field policies (enums/unions/`p_none`).                                                                                                                          |
| **Emitters**   | JSON/JSONL with optional **orjson**, sharding, metadata header when indenting; pytest fixtures with banner (seed/version/digest) and Ruff/Black formatting; JSON Schema via `model_json_schema()` with **atomic writes**. |
| **Providers**  | Built-in numbers, strings (regex via optional `rstr`), collections, temporal, identifiers. Extensible via `pfg_register_providers`.                                                                                       |
| **Strategies** | `core/strategies.py` merges schema, policies, and plugin adjustments (`pfg_modify_strategy`).                                                                                                                             |
| **Security**   | Sandbox blocks sockets, scrubs env (`NO_PROXY=*`, proxies cleared, `PYTHONSAFEPATH=1`), redirects HOME/tmp, jails filesystem writes, caps memory (`RLIMIT_AS`, `RLIMIT_DATA`), **timeout exit code 40**.                  |
| **Config**     | CLI > `PFG_*` env > `pyproject`/YAML > defaults. String booleans accepted (`true/false/1/0`).                                                                                                                             |
| **Quality**    | Mypy + Ruff; pytest across Linux/macOS/Windows, Python **3.10–3.13**; coverage ≥ **90%**.                                                                                                                                 |
| **Release**    | Hatch builds; GitHub Actions matrices; PyPI **Trusted Publishing** with signing + attestations.                                                                                                                           |

---

## Install

### pip

```bash
pip install pydantic-fixturegen
# Extras
pip install 'pydantic-fixturegen[orjson]'
pip install 'pydantic-fixturegen[regex]'
pip install 'pydantic-fixturegen[hypothesis]'
pip install 'pydantic-fixturegen[all]'        # runtime extras bundle
pip install 'pydantic-fixturegen[all-dev]'    # dev tools + runtime extras
```

### Poetry

```bash
poetry add pydantic-fixturegen
poetry run pfg --help
```

### Hatch

```toml
# pyproject.toml
[project]
dependencies = ["pydantic-fixturegen"]
```

```bash
hatch run pfg --help
```

---

## 60-second quickstart (quickstart)

**1) Define models**

```python
# models.py
from pydantic import BaseModel

class Address(BaseModel):
    street: str

class User(BaseModel):
    id: int
    name: str
    nickname: str | None = None
    address: Address
```

**2) Discover models**

```bash
pfg list ./models.py
# outputs:
# models.User
# models.Address
```

**3) Generate JSON samples**

```bash
pfg gen json ./models.py --include models.User --n 2 --indent 2 --out ./out/User
# writes out/User.json with a metadata header comment when indenting

> **Note:** When a module declares more than one model, `--include` narrows generation to the desired `module.Model`.
```

Example file (excerpt):

```json
/* seed=42 version=1.0.0 digest=<sha256> */
[
  {
    "id": 1,
    "name": "Alice",
    "nickname": null,
    "address": { "street": "42 Main St" }
  },
  {
    "id": 2,
    "name": "Bob",
    "nickname": "b",
    "address": { "street": "1 Side Rd" }
  }
]
```

**4) Generate pytest fixtures**

```bash
pfg gen fixtures ./models.py \
  --out tests/fixtures/test_user_fixtures.py \
  --style functions --scope module --cases 3 --return-type model
# produces a module with a banner and deduped imports, formatted by Ruff/Black
```

Fixture excerpt:

```python
# pydantic-fixturegen v1.0.0  seed=42  digest=<sha256>
import pytest
from models import User, Address

@pytest.fixture(scope="module", params=[0,1,2], ids=lambda i: f"user_case_{i}")
def user(request) -> User:
    # deterministic across runs/machines
    ...
```

---

## Configuration precedence (configuration-precedence)

```toml
# pyproject.toml
[tool.pydantic_fixturegen]
seed = 42
locale = "en_US"
union_policy = "weighted"
enum_policy = "random"
emitters.json.indent = 2
emitters.json.orjson = false
fixtures.style = "functions"
fixtures.scope = "module"
```

Environment variables mirror keys using `PFG_` (e.g., `PFG_SEED=99`). **CLI flags override everything**.

---

## CLI overview (cli)

- `pfg list <module_or_path>` — enumerate models (AST and/or sandboxed import).
- `pfg gen json <target>` — deterministic JSON/JSONL (`--n`, `--jsonl`, `--indent`, `--orjson/--no-orjson`, `--shard-size`, `--out`, `--seed`).
- `pfg gen schema <target>` — emit JSON Schema (`--out` required; atomic writes; `--json-errors`).
- `pfg gen fixtures <target>` — emit pytest fixtures (`--style {functions,factory,class}`, `--scope {function,module,session}`, `--p-none`, `--cases`, `--return-type {model,dict}`).
- `pfg gen explain <target>` — print provider/strategy tree per field; optional `--json` if exposed.
- `pfg doctor <target>` — audit coverage, constraints, risky imports (`--fail-on-warn`, `--json-errors`).

---

## Architecture in one diagram (architecture)

```
Models → Discovery (AST ⟷ Safe-Import Sandbox) → Strategies (policies + hooks)
      → ProviderRegistry (built-ins + plugins) → Instance Builder
      → Emitters (JSON | Fixtures | Schema, atomic IO, worker pools)
      → Artifacts on disk (with seed/version/digest metadata)
```

**Sandbox guards**: sockets blocked; env scrubbed (`NO_PROXY=*`, proxies cleared, `PYTHONSAFEPATH=1`); HOME/tmp redirected; writes outside workdir denied; memory caps (`RLIMIT_AS`, `RLIMIT_DATA`); **timeout exit code 40**.

---

## Comparison: pydantic-fixturegen vs alternatives (comparison)

| Use Case                              | Learning Curve | Determinism                                        | Security Controls                       | Best Fit                                                             |
| ------------------------------------- | -------------- | -------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------- |
| **pydantic-fixturegen**               | Low            | Strong, cascaded seeds across `random`/Faker/NumPy | Sandbox, atomic IO, JSON error taxonomy | Teams needing **deterministic Pydantic fixtures** and CLI automation |
| Hand-written fixtures                 | Medium–High    | Depends on reviewer discipline                     | None by default                         | Small codebases with few models                                      |
| Factory libraries (e.g., factory_boy) | Medium         | Often stochastic unless manually seeded            | Varies, not sandboxed                   | App-level object factories where ORM integration is key              |
| `hypothesis.extra.pydantic`           | Medium–High    | Property-based, not fixed by default               | Not sandboxed                           | Generative testing exploring model spaces                            |

---

## Community & support (community)

- Issues and contributions are welcome. Open an issue for bugs or feature discussions, and submit PRs with tests and docs.
- Security posture includes a sandbox and atomic writes; please report any bypass findings responsibly.

---

## License (license)

MIT. See `LICENSE`.

---

## Next steps (next-steps)

- Start with the **[Quickstart](./docs/quickstart.md)**.
- Dive deeper with the **[Cookbook](./docs/cookbook.md)**.
