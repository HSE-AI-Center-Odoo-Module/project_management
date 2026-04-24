# -*- coding: utf-8 -*-
"""Project Member Model
Manages team members and their roles in projects.
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

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
    is_manager = fields.Boolean(
        related='project_id.is_manager',
        store=False,
    )
    is_current_user = fields.Boolean(
        string='Is Current User',
        compute='_compute_is_current_user',
        store=False,
    )
    degree = fields.Char(
        string='Учёная степень',
        compute='_compute_profile_display',
        store=False,
    )
    academic_direction = fields.Char(
        string='Научное направление',
        compute='_compute_profile_display',
        store=False,
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
                    _("You cannot add an inactive user to the team.")
                )

    # ========== COMPUTES ==========
    @api.depends_context('uid')
    def _compute_is_current_user(self):
        for member in self:
            member.is_current_user = (member.user_id.id == self.env.uid)

    @api.depends('user_id')
    def _compute_profile_display(self):
        """Pull degree label and academic_direction from employee profile for team list display."""
        user_ids = self.mapped('user_id').ids
        if not user_ids:
            for member in self:
                member.degree = ''
                member.academic_direction = ''
            return

        profiles = self.env['university.employee.profile'].sudo().search(
            [('user_id', 'in', user_ids)]
        )
        profile_by_user = {p.user_id.id: p for p in profiles}
        degree_labels = dict(
            self.env['university.employee.profile'].fields_get(['degree'])['degree']['selection']
        )
        for member in self:
            profile = profile_by_user.get(member.user_id.id)
            if profile:
                member.degree = degree_labels.get(profile.degree, '') if profile.degree else ''
                member.academic_direction = profile.academic_direction or ''
            else:
                member.degree = ''
                member.academic_direction = ''

    # ========== ACTIONS ==========
    def action_open_employee_profile(self):
        """Open employee profile dialog. Edit mode for self/admin; readonly for managers."""
        self.ensure_one()
        is_admin = self.env.user.has_group('project_management.administrator')
        is_self = self.user_id.id == self.env.uid
        is_manager = self.env.user in self.project_id.project_manager_id

        if not (is_admin or is_self or is_manager):
            raise AccessError(_("You do not have access to view this employee profile."))

        # Lazy find-or-create with race-condition safety via savepoint
        profile = self.env['university.employee.profile'].sudo().search(
            [('user_id', '=', self.user_id.id)], limit=1
        )
        if not profile:
            try:
                with self.env.cr.savepoint():
                    profile = self.env['university.employee.profile'].sudo().create(
                        {'user_id': self.user_id.id}
                    )
            except Exception:
                profile = self.env['university.employee.profile'].sudo().search(
                    [('user_id', '=', self.user_id.id)], limit=1
                )

        form_mode = 'edit' if (is_admin or is_self) else 'readonly'

        return {
            'type': 'ir.actions.act_window',
            'name': _('Employee Profile'),
            'res_model': 'university.employee.profile',
            'res_id': profile.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': form_mode},
        }
