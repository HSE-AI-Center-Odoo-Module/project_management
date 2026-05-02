# -*- coding: utf-8 -*-
from odoo import api, fields, models


class UniversityProjectTrl(models.Model):
    _name = 'university.project.trl'
    _description = 'Technology Readiness Level (УГТ)'
    _order = 'level'
    _rec_name = 'display_name'

    level = fields.Integer(string='Уровень', required=True)
    name = fields.Char(string='Описание', required=True)
    display_name = fields.Char(
        string='УГТ',
        compute='_compute_display_name',
        store=True,
    )

    _sql_constraints = [
        ('uniq_level', 'unique(level)', 'Уровень УГТ с таким номером уже существует.'),
    ]

    @api.depends('level', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"УГТ {rec.level} — {rec.name}" if rec.level and rec.name else rec.name or ''

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            try:
                level_num = int(name)
                domain = [('level', '=', level_num)] + domain
            except ValueError:
                domain = [('name', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)
