# -*- coding: utf-8 -*-
from odoo import fields, models, api

class UniversityProjectDocument(models.Model):
    _name = "university.project.document"
    _description = "Project Document Attachment"
    _order = "id desc"

    name = fields.Char(string="Description", required=True)
    
    # Поля для хранения файла
    file_data = fields.Binary(string="File", required=True)
    file_name = fields.Char(string="File Name") 
    
    # СВЯЗИ
    # Убираем required=True, так как документ может быть привязан либо к проекту, либо к этапу
    project_id = fields.Many2one(
        "project.project", 
        string="Project", 
        ondelete="cascade"
    )

    stage_id = fields.Many2one(
        'university.project.stage', 
        string="Stage", 
        ondelete="cascade"
    )

    # Автоматически устанавливаем проект из этапа, если он выбран
    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id:
            self.project_id = self.stage_id.project_id