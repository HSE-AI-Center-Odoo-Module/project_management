# -*- coding: utf-8 -*-
"""Employee Academic/Professional Profile"""
from odoo import _, api, fields, models

DEGREE_SELECTION = [
    ('bachelor', 'Бакалавр'),
    ('master', 'Магистр'),
    ('candidate', 'Кандидат наук'),
    ('doctor', 'Доктор наук'),
]


class UniversityEmployeeProfile(models.Model):
    _name = 'university.employee.profile'
    _description = 'University Employee Profile'
    _rec_name = 'user_id'
    _order = 'user_id'

    # ========== IDENTITY ==========
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ========== PROFESSIONAL INFO ==========
    position = fields.Char(string='Должность')
    department = fields.Char(string='Кафедра / Лаборатория')

    # ========== ACADEMIC INFO ==========
    degree = fields.Selection(DEGREE_SELECTION, string='Учёная степень')
    academic_direction = fields.Char(string='Научное направление')
    specialization = fields.Char(string='Специализация')

    # ========== CERTIFICATIONS ==========
    certification_ids = fields.One2many(
        'university.employee.certification',
        'profile_id',
        string='Сертификаты',
    )

    # ========== COMPUTED — WORKLOAD ==========
    active_task_count = fields.Integer(
        string='Активных задач',
        compute='_compute_workload',
        store=False,
    )
    workload_percent = fields.Float(
        string='Загруженность, %',
        compute='_compute_workload',
        store=False,
        digits=(5, 1),
    )

    # ========== COMPUTED — PROJECT HISTORY ==========
    project_count = fields.Integer(
        string='Проектов',
        compute='_compute_project_data',
        store=False,
    )
    project_ids = fields.Many2many(
        'project.project',
        string='Проекты',
        compute='_compute_project_data',
        store=False,
    )

    # ========== SQL CONSTRAINTS ==========
    _sql_constraints = [
        (
            'uniq_user_profile',
            'unique(user_id)',
            'A profile already exists for this user.',
        ),
    ]

    # ========== COMPUTES ==========
    @api.depends('user_id')
    def _compute_workload(self):
        for profile in self:
            if not profile.user_id:
                profile.active_task_count = 0
                profile.workload_percent = 0.0
                continue
            # sudo() required — viewer may not have task read access for other users' tasks
            # stage_id.fold=True marks done/archived stages (is_closed does not exist in this build)
            tasks = self.env['project.task'].sudo().search([
                ('user_ids', 'in', profile.user_id.id),
                ('stage_id.fold', '=', False),
            ])
            count = len(tasks)
            profile.active_task_count = count
            profile.workload_percent = min(count / 5.0 * 100.0, 100.0)

    @api.depends('user_id')
    def _compute_project_data(self):
        for profile in self:
            if not profile.user_id:
                profile.project_ids = False
                profile.project_count = 0
                continue
            # sudo() required — manager viewing a member's profile may not see all their projects
            members = self.env['university.project.member'].sudo().search([
                ('user_id', '=', profile.user_id.id),
            ])
            projects = members.mapped('project_id')
            profile.project_ids = projects
            profile.project_count = len(projects)
