# -*- coding: utf-8 -*-
from odoo import fields, models


class UniversityProjectLink(models.Model):
    _name = "university.project.link"
    _description = "University project link"

    name = fields.Char(string="Название ресурса", required=True)
    url = fields.Char(string="Ссылка", required=True)
    project_id = fields.Many2one("project.project", string="Project", ondelete="cascade")