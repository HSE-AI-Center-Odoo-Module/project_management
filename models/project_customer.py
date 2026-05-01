# -*- coding: utf-8 -*-
"""Project Customer Model
Defines external customers/organizations.
"""
from odoo import models, fields


class ProjectCustomer(models.Model):
    _name = 'university.project.customer'
    _description = 'University Project Customer'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Название организации', required=True)
    contact_person = fields.Char(string='Контактное лицо')
    email = fields.Char(string='Email')
    active = fields.Boolean(default=True)