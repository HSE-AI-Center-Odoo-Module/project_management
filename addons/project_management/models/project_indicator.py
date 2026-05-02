# -*- coding: utf-8 -*-
from odoo import fields, models


class UniversityProjectIndicator(models.Model):
    _name = 'university.project.indicator'
    _description = 'Project Performance Indicator'
    _order = 'sequence, id'

    project_id = fields.Many2one(
        'project.project', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Наименование показателя', required=True)
    unit = fields.Char(string='Единица измерения')
    method = fields.Text(string='Методика расчёта')
    planned_value = fields.Char(string='Плановое значение')
    actual_value = fields.Char(string='Фактически достигнутое значение')
    justification_doc = fields.Char(string='Документ-обоснование (наименование и №)')
