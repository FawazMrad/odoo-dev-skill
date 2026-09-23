# Version notes (16 to 19)

Pointers only. Always confirm in the local source of the exact version before relying on one.

## 16.0
- Views: `attrs="{'invisible': [...]}"`, `states="..."`.
- Lists: `<tree>`, view_mode `tree`.
- Display name: `name_get()`.
- Form tests: `from odoo.tests.common import Form`.

## 17.0
- `attrs` and `states` removed. Use expressions: `invisible="state != 'draft'"`,
  `readonly="..."`, `required="..."`, `column_invisible` in lists.
- `name_get` deprecated. Use `_compute_display_name` with `@api.depends`.
- `from odoo.tests import Form`.
- Still `<tree>`.
- OWL 2; patches: `patch(Component.prototype, { ... })`.

## 18.0
- `<tree>` → `<list>`; view_mode `list`; actions `view_mode="list,form"`.
- `group_operator` → `aggregator` on fields.
- `<chatter/>` shorthand in forms.
- Check `_read_group` / `read_group` signatures in source before use.

## 19.0
- `_sql_constraints` → `models.Constraint` / `models.Index` class attributes.
- `res.users.groups_id` → `group_ids`.
- More 17/18 deprecations removed: grep source before assuming any API exists.

## Migrating a module between versions
- Grep the target version for every overridden method; signatures change.
- Recheck every xpath anchor against the target version's view.
- Use `migrations/<version>/` scripts for data changes.
