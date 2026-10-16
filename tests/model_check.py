"""Actual local model evidence. Run from repository root: python3 tests/model_check.py."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import json
from datetime import datetime, timezone
from pathlib import Path
from core import Store, local_suggest, Invalid

root = Path(__file__).resolve().parents[1]
evidence = {'checked_at': datetime.now(timezone.utc).isoformat(), 'model': 'phi3:latest',
            'data': 'Fictional English subtitles. No customers, no production benchmark.', 'cases': []}
cases = [
    ('In order to get started, you will need to press the green button on the Solara panel.', 70, ['Solara']),
    ('Please make sure that you do not turn off the power until the light stops flashing.', 70, []),
    ('Wait 10 seconds before you open it.', 14, []),
    ('The Riverside studio opens at 10 and closes at 20.', 50, ['Riverside']),
]
for source, budget, glossary in cases:
    case = {'source': source, 'target_characters': budget, 'protected_terms': glossary}
    try:
        case['result'] = local_suggest(source, budget, glossary)
        case['accepted_by_guards'] = True
    except Invalid as exc:
        case['accepted_by_guards'] = False
        case['error'] = str(exc)
    evidence['cases'].append(case)
    (root / 'evidence' / 'model-check.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(case), flush=True)
