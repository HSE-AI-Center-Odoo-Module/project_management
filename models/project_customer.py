# -*- coding: utf-8 -*-
"""Project Customer Model
Defines external customers/organizations.
"""
from odoo import models, fields


class ProjectCustomer(models.Model):
    """Base reference: customer/organization definition"""
    _name = 'university.project.customer'
    _description = 'University Project Customer'
    _order = 'name'

    # ========== FIELDS ==========
    name = fields.Char(
        string='Organization Name',
        required=True
    )
    contact_person = fields.Char(
        string='Contact Person'
    )
    email = fields.Char(
        string='Email'
    )
    active = fields.Boolean(
        default=True,
        help="Whether customer is active"
    )