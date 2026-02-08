# -*- coding: utf-8 -*-
"""Project Role Model
Defines user roles in projects (e.g., owner, manager, member, viewer).
"""
from odoo import fields, models


class UniversityProjectRole(models.Model):
    """Base reference: project role definition"""
    _name = "university.project.role"
    _description = "University project role"
    _order = "sequence, name"

    # ========== FIELDS ==========
    name = fields.Char(
        string="Role Name",
        required=True
    )
    code = fields.Char(
        string="Technical Code",
        required=True,
        help="Technical code: owner, manager, member, viewer"
    )
    sequence = fields.Integer(
        default=10,
        help="Ordering for role display"
    )
    active = fields.Boolean(
        default=True,
        help="Whether role is active"
    )
