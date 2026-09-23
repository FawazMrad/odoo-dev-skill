# OCA / Odoo conventions

The correctness rules below are enforced. The naming conventions at the bottom are
**opt-in**: follow the pattern already used in the repo, and only apply them when the repo
already does, or when the user asks.

## Python structure

Attribute order inside a model:
1. private attributes (`_name`, `_inherit`, `_description`, `_order`)
2. field declarations
3. constraints (`_sql_constraints`, or `models.Constraint` in 19)
4. default methods
5. compute and search methods, same order as the fields
6. `@api.constrains` and `@api.onchange`
7. CRUD overrides (`create`, `write`, `unlink`)
8. action methods
9. other business methods

Method naming: `_compute_<field>`, `_inverse_<field>`, `_search_<field>`, `_default_<field>`,
`_onchange_<field>`, `_check_<constraint>`, `action_<something>` (with `self.ensure_one()`
when it acts on one record).

Fields: `_id` suffix for Many2one, `_ids` for One2many/Many2many. Drop `string=` when it
matches the field name. Defaults as `default=lambda self: self._default_x()` so they stay
inheritable.

Imports, in order: stdlib, third party, `odoo`, `odoo.addons`, local (`from . import x`),
then optional dependencies inside try/except with `_logger.debug(err)`.

## Python safety

- **No SQL injection**: never build SQL with `+` or `%`. Pass parameters:
  `cr.execute('... WHERE id IN %s', (tuple(ids),))`.
- **Don't bypass the ORM**: use `search`/`read_group` instead of raw SQL unless the ORM
  genuinely can't do it, and say why in a comment.
- **Never `cr.commit()`**: the framework owns the transaction. Use `cr.savepoint()`, or an
  isolated cursor when truly needed, with a comment explaining why.
- **No bare `except: pass`**: log it (`_logger.debug(..., exc_info=1)`) or handle it.
- **`%`-style formatting** for translatable strings, not `.format()`, and prefer named
  placeholders: `_('Missing %(field)s', field=...)`.
- Refactor a method that grows too long or too nested instead of adding comments to explain it.

## Views

- `position="replace"` on a core element needs a comment saying why it's unavoidable **and**
  `priority` above 100, so other inheriting views don't break.
- Don't prefix an XML ID with the current module's name inside that same module.
- One module extends a given view once; add to the existing inherited view instead of a second one.
- Hide with `invisible="1"` rather than removing a field other logic needs.

## Tests

- A bug fix ships with a test that fails without the fix.
- Dates: use `freeze_time` (freezegun, bundled since 14.0) instead of `now()`/`today()`.
- External services: mock them (`self.patch`, `cls.classPatch`, `unittest.mock`). Never call a
  real API in a test.
- Run with the lowest permissions that make sense: `new_test_user`, the `@users` decorator, or
  set `uid`/`env` in `setUpClass`. Admin-only tests hide access errors real users will hit.
- Records built in `setUpClass` keep the old `env`: use `record.with_env(self.env)` after
  switching user, or the access assertions are meaningless.
- No demo data; create what the test needs.
- Beware `subTest` (and decorators built on it): the cursor and cache aren't reset between
  subtests.

## Manifest and hooks

- Version as `<odoo>.x.y.z`: bump **x** for model/view changes needing migration, **y** for new
  backward-compatible features, **z** for fixes.
- Breaking change = migration script, or at minimum a note about what needs migrating.
- Put `pre_init_hook`, `post_init_hook`, `uninstall_hook`, `post_load` in `hooks.py` at the
  module root, imported in `__init__.py`.
- External libs: `external_dependencies` in the manifest plus `requirements.txt` at the repo
  root. Don't pin exact versions; a lower bound only if a recent feature is needed.

## Opt-in naming conventions (only if the repo already uses them)

- XML IDs: `<model>_view_form`, `<model>_view_list`, `<model>_action`, `<model>_menu`,
  `<model>_group_user`, `<model>_rule_company`, data records `<model>_<record_name>`,
  demo records suffixed `_demo`.
- Files: one per model, `models/sale_order.py`, `views/sale_order_views.xml`,
  `data/<model>_data.xml`, plus `security/`, `wizards/`, `reports/`, `controllers/`.
- Module names: singular, prefixed with the module being extended (`sale_something`), `base_`
  for base modules, `l10n_CC_` for localizations.
