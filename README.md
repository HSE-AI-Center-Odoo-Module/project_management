# Project Management (Odoo 18) 🚀

Custom Odoo module for AI Research Centre project operations.

## Overview 🧩

The module extends `project.project` and `project.task` with:
- project passport fields (type, customer, dates, external links)
- team model with explicit project roles
- custom project stages with history log
- custom task board/form behavior
- role-based visibility for projects and tasks
- documents and links attached to project, stage, and task

## Dependencies 📦

Defined in `__manifest__.py`:
- `base`
- `project`
- `mail`

## Main Models 🗂️

Custom models:
- `university.project.role`
- `university.project.type`
- `university.project.customer`
- `university.project.member`
- `university.project.stage`
- `university.project.stage.history`
- `university.project.document`
- `university.project.link`

Extended core models:
- `project.project`
- `project.task`
- `res.users`

## Security Model 🔐

Groups:
- `project_management.employee`
- `project_management.administrator`

Access layers:
- ACL in `security/ir.model.access.csv`
- Record rules in `security/security.xml`

Key behavior:
- Employees see projects where they are members.
- Project managers get edit access to their projects.
- Employee task visibility is assignment-based (`user_ids`).
- PM/Admin can see full task board for project context.

## Project Manager Logic 👥

`project_manager_id` is synchronized with team role data:
- compute: users with role code `manager` are included in `project_manager_id`
- inverse: if user is set in `project_manager_id`, they are added/updated in team with role `manager`

A seed role with `code = manager` is provided in `data/project_role_data.xml`.
Role code uniqueness is enforced by SQL constraint.

## Menus and UI 🖥️

Root menu: `AI Research Centre`
- Projects
- Configuration (roles, types, customers, users)

Important views:
- custom project list/kanban/form
- custom task kanban and task form
- custom stage form with history tab

## Installation / Update ⚙️

1. Add `addons/project_management` to Odoo addons path.
2. Update app list.
3. Install module `project_management`.

For updates during development:
```bash
odoo -u project_management -d <db_name>
```

## Tests ✅

Test package:
- `tests/test_task_board_access.py`

Current coverage:
- task board domain matrix for `employee` / PM / `administrator`

Run tests (example):
```bash
odoo -d <db_name> -u project_management --test-enable --stop-after-init
```

## Localization 🌐

Translations are in:
- `i18n/ru.po`

User-facing validation messages are wrapped with `_()` and included in RU translations.

## Notes 📝

- If role data already contains duplicate role codes, module update can fail because of unique constraint on role `code`.
- Ensure only one role uses `code = manager`.

