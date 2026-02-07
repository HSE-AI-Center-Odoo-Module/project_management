# -*- coding: utf-8 -*-
from odoo import fields, models


class UniversityProjectRole(models.Model):
    _name = "university.project.role"
    _description = "University project role"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Technical code, e.g. owner, manager, member, viewer")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
