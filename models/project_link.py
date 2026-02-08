# -*- coding: utf-8 -*-
"""Project Link Model
Stores external URL references for projects.
"""
from odoo import fields, models


class UniversityProjectLink(models.Model):
    """External URL reference linked to project"""
    _name = "university.project.link"
    _description = "University project link"

    # ========== FIELDS ==========
    name = fields.Char(
        string="Name",
        required=True
    )
    url = fields.Char(
        string="URL",
        required=True
    )

    # ========== RELATIONS ==========
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        ondelete="cascade"
    )