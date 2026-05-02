# -*- coding: utf-8 -*-
from odoo import api, fields, models


class UniversityProjectDivision(models.Model):
    _name = 'university.project.division'
    _description = 'University Division / Laboratory'
    _order = 'code, name'
    _rec_name = 'display_name_full'

    code = fields.Char(string='Код подразделения', required=True)
    name = fields.Char(string='Наименование', required=True)
    display_name_full = fields.Char(
        string='Подразделение',
        compute='_compute_display_name_full',
        store=True,
    )

    _sql_constraints = [
        ('uniq_code', 'unique(code)', 'Подразделение с таким кодом уже существует.'),
    ]

    @api.depends('code', 'name')
    def _compute_display_name_full(self):
        for rec in self:
            rec.display_name_full = f"{rec.code} — {rec.name}" if rec.code and rec.name else rec.name or rec.code or ''

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)
