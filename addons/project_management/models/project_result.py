# -*- coding: utf-8 -*-
from odoo import fields, models

RESULT_TYPE = [
    ('scientific', 'Научно-технический'),
    ('educational', 'Образовательный'),
]


class UniversityProjectResult(models.Model):
    _name = 'university.project.result'
    _description = 'Project Result'
    _order = 'result_type, sequence, id'

    project_id = fields.Many2one(
        'project.project', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    result_type = fields.Selection(RESULT_TYPE, string='Тип', required=True, default='scientific')
    name = fields.Char(string='Наименование результата', required=True)
    planned_value = fields.Text(string='Плановое значение')
    actual_value = fields.Text(string='Фактическое значение')
