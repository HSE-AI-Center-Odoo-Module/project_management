# -*- coding: utf-8 -*-
"""Project Member Model
Manages team members and their roles in projects.
"""
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class UniversityProjectMember(models.Model):
    """Project team member with assigned role"""
    _name = "university.project.member"
    _description = "University project member"
    _rec_name = "user_id"
    _order = "project_id, id"

    # ========== RELATIONS ==========
    project_id = fields.Many2one(
        "project.project",
        required=True,
        ondelete="cascade",
        index=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        ondelete="restrict",
        index=True
    )
    role_id = fields.Many2one(
        "university.project.role",
        string="Role",
        required=True,
        ondelete="restrict"
    )

    # ========== COMPUTED FIELDS ==========
    role_code = fields.Char(
        related="role_id.code",
        store=True,
        readonly=True,
        help="Technical role code"
    )

    # ========== CONSTRAINTS ==========
    _sql_constraints = [
        (
            "uniq_project_user",
            "unique(project_id, user_id)",
            "User is already in project team."
        ),
    ]

    # ========== VALIDATIONS ==========
    @api.constrains("project_id", "user_id")
    def _check_user_active(self):
        """Ensure only active users can be added to team"""
        for rec in self:
            if rec.user_id and not rec.user_id.active:
                raise ValidationError(
                    "You cannot add an inactive user to the team."
                )
