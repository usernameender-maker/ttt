## Phrase template communication for navigation and travel

`ievf.phrase_communication` provides a deterministic catalog for navigation and
travel commands. It matches explicit phrases to structured message intents and
returns the resolved template and slot values. This is a compact communication
layer for ordered actions, not a full conversational AI.

### Stage structure

- `basic`: direct movement and halt commands
- `travel`: route and destination phrases
- `order`: operational guidance and holding actions
- `space`: orbital and sector navigation phrases

### Example usage

```python
from ievf.phrase_communication import determine_phrase

print(determine_phrase("turn left", "en"))
print(determine_phrase("travel to docking bay 3", "en"))
print(determine_phrase("muevete al sector gamma", "es"))
```

The catalog is explicit and deterministic. If a phrase matches no template, or
matches more than one template, it raises `ValueError` instead of guessing.

```sh
python -m unittest discover -s tests -p test_phrase_communication.py -v
```
