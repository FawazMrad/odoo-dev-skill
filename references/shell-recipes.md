# Read-only odoo-bin shell recipes

Run on the **staging** branch by default (Odoo.sh → branch → Shell tab).

## Safety template (every script)
```bash
odoo-bin shell --no-http <<'PY'
env.cr.rollback()
env.cr.execute("SET TRANSACTION READ ONLY")   # any write now fails

# --- queries ---

env.cr.rollback()
PY
```
Never use in these scripts: `create`, `write`, `unlink`, `copy`, `action_*`, `button_*`,
`message_post`, `send_mail`, `env.cr.commit()`, module install/upgrade/uninstall.
Limit output (`limit=`, chosen fields). Add `-d <db>` only if the shell asks for it.

## Installed modules
```python
for m in env['ir.module.module'].search([('state', '=', 'installed')], order='name'):
    print(m.name, m.installed_version, m.author)
```

## Fields of a model (code + custom + Studio)
```python
M = 'sale.order'
for f in env['ir.model.fields'].search([('model', '=', M)], order='name'):
    print(f.name, f.ttype, f.relation or '', f.state, f.store, f.modules)
```
`state = 'manual'` means created in DB (Studio/UI).

## All Studio/custom fields
```python
for f in env['ir.model.fields'].search([('state', '=', 'manual')], order='model,name'):
    print(f.model, f.name, f.ttype)
```

## Views inheriting a view (tree)
```python
def walk(v, d=0):
    for c in v.inherit_children_ids:
        print('  ' * d, c.id, c.key or c.name, 'prio', c.priority, 'active', c.active)
        walk(c, d + 1)
walk(env.ref('sale.view_order_form'))
```

## Final merged arch
```python
print(env['sale.order'].get_view(view_type='form')['arch'])          # 17+
# 16: print(env['sale.order'].fields_view_get(view_type='form')['arch'])
```

## Automations and server actions on a model
```python
M = 'sale.order'
for a in env['base.automation'].search([('model_id.model', '=', M)]):
    print('AUTO', a.id, a.name, a.trigger, a.active)
for a in env['ir.actions.server'].search([('model_id.model', '=', M)]):
    print('SRV', a.id, a.name, a.state)
    if a.state == 'code':
        print(a.code)
```

## Sample records
```python
print(env['sale.order'].search([], limit=5, order='id desc').read(['name', 'state', 'amount_total']))
```

## Value distribution
```python
print(env['sale.order'].read_group([], ['state'], ['state']))
```

## XML IDs
```python
print(env['ir.model.data'].search([('module', '=', 'sale'), ('name', 'ilike', 'order_form')]).read(['module', 'name', 'model', 'res_id']))
```

## Access and record rules
```python
M = 'sale.order'
for r in env['ir.rule'].search([('model_id.model', '=', M)]):
    print('RULE', r.name, r.domain_force, r.groups.mapped('name'), r.active)
for a in env['ir.model.access'].search([('model_id.model', '=', M)]):
    print('ACL', a.name, a.group_id.name, a.perm_read, a.perm_write, a.perm_create, a.perm_unlink)
```

## Crons on a model
```python
for c in env['ir.cron'].search([('model_id.model', '=', 'sale.order')]):
    print(c.name, c.active, c.interval_number, c.interval_type)
```

## Reports of a model
```python
for r in env['ir.actions.report'].search([('model', '=', 'sale.order')]):
    print(r.id, r.name, r.report_name, r.report_type, r.paperformat_id.name)
```

## Custom investigations
Same template. Read only (`search`, `read`, `read_group`, `mapped`, `SELECT`).
Tell the user what it checks and which output to paste back.
