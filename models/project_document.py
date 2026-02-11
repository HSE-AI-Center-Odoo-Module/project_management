# -*- coding: utf-8 -*-
"""Project Document Model
Handles document storage for projects and stages.
"""
from odoo import fields, models, api


class UniversityProjectDocument(models.Model):
    """Document attachment to projects or stages"""
    _name = "university.project.document"
    _description = "Project Document Attachment"
    _order = "id desc"

    # ========== BASIC FIELDS ==========
    name = fields.Char(
        string="Description",
        required=True
    )

    # ========== FILE STORAGE ==========
    file_data = fields.Binary(
        string="File",
        required=True
    )
    file_name = fields.Char(
        string="File Name"
    )

    # ========== RELATIONS ==========
    # Document can be linked to project or stage
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

    task_id = fields.Many2one(
        'project.task', 
        string="Задача", 
        ondelete='cascade'
    )

    # ========== METHODS ==========
    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Auto-fill project from selected stage"""
        if self.stage_id:
            self.project_id = self.stage_id.project_id