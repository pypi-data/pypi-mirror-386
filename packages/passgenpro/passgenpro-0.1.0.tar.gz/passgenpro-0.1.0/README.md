# passgenpro 🔐

A simple but powerful Python password generator.

## Usage

```python
from passgenpro.generator import generate

print(generate())               # 12 simvolluq random parol
print(generate(16, symbols=False))  # simvollar olmadan
