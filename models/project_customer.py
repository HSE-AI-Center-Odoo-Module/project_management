from odoo import models, fields

class ProjectCustomer(models.Model):
    _name = 'university.project.customer'
    _description = 'University Project Customer'
    _order = 'name'

    name = fields.Char(string='Organization Name', required=True)
    contact_person = fields.Char(string='Contact Person')
    email = fields.Char(string='Email')
    active = fields.Boolean(default=True)