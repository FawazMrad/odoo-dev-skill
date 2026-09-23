# Safe inheritance checklist

## Models
- Extend with `_inherit = 'x.model'` and no `_name`. Never `_name = 'existing.model'` alone.
- Never change an existing field's type: Postgres converts or drops the values.
- `required=True` on an existing field needs a `default` and a migration filling old rows.
- Renaming a field needs a migration script, otherwise data stays in the old column and the
  new field starts empty.
- Removing a field hides its data from the ORM. Confirm with the user first.
- Stored computes on big tables: warn about upgrade time.
- Think about `ondelete` on Many2one for existing records.
- No `uninstall_hook` or migration that deletes records unless asked.

## Overrides
```python
def action_confirm(self):
    res = super().action_confirm()
    # our logic
    return res
```
- Keep the original signature (check source; use `*args, **kwargs` if it varies).
- `create`: `@api.model_create_multi`, handle `vals_list`.
- `write` calling `write`: guard with a context key to avoid loops.
- Other custom modules overriding the same method run in dependency order. If order matters,
  fix `depends`, don't hack around it.

## Views
- Anchor xpath on names: `//field[@name='partner_id']`. Avoid index-based paths.
- Prefer `after`, `before`, `inside`, `attributes` over `replace`.
- Find other inheritors first: grep core, enterprise and repo for `inherit_id="module.view"`,
  and the "inherited views" shell recipe for Studio/DB views.
- If another view moves or removes your anchor, inherit the resulting structure or set `priority`.
- Don't remove fields other logic needs in the view; hide them instead.

## Studio and DB-only customizations
- `x_*` / `x_studio_*` fields exist only in the DB. Check before adding a field with a
  similar meaning, and ask the user whether to reuse it.
- Automated actions and server actions may write the same fields. Check before adding
  computes/onchanges on them.

## Security
- New model: access rows for each relevant group.
- Company-bound data: record rules.
- `sudo()` only where needed, with a short reason comment.
