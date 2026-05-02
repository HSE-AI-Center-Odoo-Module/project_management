# -*- coding: utf-8 -*-
from odoo import fields, models

SIGN_TYPE = [
    ('approves', 'Утверждает'),
    ('agrees', 'Согласует'),
    ('signs', 'Подписывает'),
]


class UniversityProjectSignatory(models.Model):
    _name = 'university.project.signatory'
    _description = 'Project Signatory'
    _order = 'sequence, id'

    project_id = fields.Many2one(
        'project.project', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one('res.users', string='Сотрудник', required=True)
    position = fields.Char(string='Должность / Роль')
    sign_type = fields.Selection(SIGN_TYPE, string='Тип подписи', required=True, default='signs')
    from_partner = fields.Boolean(string='От партнёра')
