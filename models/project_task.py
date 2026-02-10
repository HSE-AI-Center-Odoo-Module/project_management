from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = "project.task"

    # Техническое поле для фильтрации исполнителей (вы уже его создали)
    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids",
        string="Allowed Assignees",
        readonly=True
    )

    # Добавим приоритет (звездочки), если его нет
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], default='0', string="Priority")