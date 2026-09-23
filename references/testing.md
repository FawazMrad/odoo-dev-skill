# Testing standard

## By size
- **Small**: no tests unless Python logic changed. If it did, one focused test.
- **Medium**: tests for every added/changed behavior + items 2, 3, 6 below.
- **Large**: everything below.

## Layout
```
module_name/tests/
  __init__.py        # imports every test file
  common.py          # shared setUpClass data
  test_<feature>.py
```

## Base
```python
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError, ValidationError

@tagged('post_install', '-at_install')
class TestFeature(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # minimal data, built once
```
`Form` import path differs per version (see version-notes).

## Coverage checklist
1. **Happy path**: the scenario the customer described.
2. **Edge cases**: empty/False values, zero and negative numbers, archived records,
   duplicates, boundary dates, rounding, other currencies, unicode text.
3. **Multi-record**: run on 2+ records at once.
4. **Access rights**: `with_user` per relevant group; assert `AccessError` where blocked.
5. **Multi-company**: when the model has `company_id`.
6. **Errors**: `assertRaises` for each constraint and `UserError` path added.
7. **Regression**: the core flow you touched still works (confirm, invoice, validate...).
8. **Computes**: change a dependency, assert recompute.
9. **Reports**: render the report (check `_render_qweb_pdf`/`_render_qweb_html` signature in
   source) and assert key values appear.

Rules:
- Name tests by behavior: `test_discount_locked_after_confirm`.
- Never rely on demo data or the live DB. Create what you need.
- Instance-only data (Studio fields, specific config): check its shape via shell, then
  recreate it in `setUpClass`.

## Run locally
```bash
./odoo-bin -c <conf> -d test_<module> -i <module> \
  --test-enable --stop-after-init --test-tags /<module> --log-level=test
```
Throwaway DB only. Report the real pass/fail summary. Fix and rerun until green.
