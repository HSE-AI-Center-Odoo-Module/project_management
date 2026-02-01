# -*- coding: utf-8 -*-
from odoo import fields, models


class UniversityProjectRole(models.Model):
    _name = "university.project.role"
    _description = "University project role"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(help="Technical code, e.g. owner, manager, member, viewer")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # MVP-права на уровне проекта/задач (упрощенно)
    can_read_project = fields.Boolean(default=True)
    can_write_project = fields.Boolean(default=False)
    can_read_tasks = fields.Boolean(default=True)
    can_write_tasks = fields.Boolean(default=False)
