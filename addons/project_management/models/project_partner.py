# -*- coding: utf-8 -*-
from odoo import fields, models


class UniversityProjectPartner(models.Model):
    _name = 'university.project.partner'
    _description = 'Project Partner'
    _order = 'sequence, id'

    project_id = fields.Many2one(
        'project.project', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Организация', required=True)
    country_id = fields.Many2one('res.country', string='Страна')
    consortium = fields.Char(string='Консорциум')
    role = fields.Char(string='Роль в проекте')
    funding = fields.Monetary(string='Финансирование', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Валюта',
        default=lambda self: self.env.ref('base.RUB', raise_if_not_found=False),
    )
