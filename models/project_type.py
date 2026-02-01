from odoo import models, fields

class ProjectType(models.Model):
    _name = 'university.project.type'
    _description = 'University Project Type'
    _order = 'name'

    name = fields.Char(string='Type Name', required=True, translate=True)
    active = fields.Boolean(default=True)