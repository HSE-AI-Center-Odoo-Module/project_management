# -*- coding: utf-8 -*-
from odoo import fields, models

class UniversityProjectDocument(models.Model):
    _name = "university.project.document"
    _description = "Project Document Attachment"
    _order = "name"

    name = fields.Char(string="Filename", required=True)
    
    # КЛЮЧЕВОЕ ПОЛЕ: для загрузки и хранения самого файла
    file_data = fields.Binary(string="File", required=True)
    file_name = fields.Char(string="Filename") # для хранения имени файла
    
    # СВЯЗЬ: Many2one, которая связывает вложение с конкретным проектом
    project_id = fields.Many2one(
        "project.project", 
        string="Project", 
        ondelete="cascade", 
        required=True
    )