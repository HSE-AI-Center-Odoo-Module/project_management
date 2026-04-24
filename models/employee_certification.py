# -*- coding: utf-8 -*-
"""Employee Certification Model"""
from odoo import fields, models


class UniversityEmployeeCertification(models.Model):
    _name = 'university.employee.certification'
    _description = 'Employee Certification'
    _rec_name = 'name'
    _order = 'issue_date desc, id desc'

    # ========== RELATIONS ==========
    profile_id = fields.Many2one(
        'university.employee.profile',
        string='Profile',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ========== CERTIFICATION DATA ==========
    name = fields.Char(string='Название сертификата', required=True)
    issuer = fields.Char(string='Выдан кем')
    issue_date = fields.Date(string='Дата выдачи')
    expiry_date = fields.Date(string='Действует до')

    # ========== FILE ==========
    file_data = fields.Binary(string='Файл сертификата')
    file_name = fields.Char(string='Имя файла')
