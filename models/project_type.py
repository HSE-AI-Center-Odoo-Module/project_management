# -*- coding: utf-8 -*-
"""Project Type Model
Defines available project types for classification.
"""
from odoo import models, fields


class ProjectType(models.Model):
    """Base reference: project type definition"""
    _name = 'university.project.type'
    _description = 'University Project Type'
    _order = 'name'

    # ========== FIELDS ==========
    name = fields.Char(
        string='Type Name',
        required=True,
        translate=True
    )
    active = fields.Boolean(
        default=True,
        help="Whether project type is available"
    )