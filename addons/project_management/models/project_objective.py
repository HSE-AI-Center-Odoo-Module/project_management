# -*- coding: utf-8 -*-
from odoo import fields, models


class UniversityProjectObjective(models.Model):
    _name = 'university.project.objective'
    _description = 'Project Objective (Task)'
    _order = 'sequence, id'

    project_id = fields.Many2one(
        'project.project', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Задача', required=True)
    description = fields.Text(string='Описание')
