from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Project(models.Model):
    _inherit = "project.project"

    # --- Ваши существующие поля ---
    name_en = fields.Char(string="Name (EN)")
    project_type = fields.Selection([
        ('research', 'Research'),
        ('dev', 'Development'),
        ('education', 'Education')
    ], string="Тип проекта", default='dev')
    
    project_status = fields.Selection([
        ('draft', 'Черновик'),
        ('active', 'Активен'),
        ('done', 'Завершен'),
        ('cancel', 'Отменен')
    ], string="Статус", default='draft')

    link_repo = fields.Char(string="Репозиторий")
    link_docs = fields.Char(string="Документация")
    link_design = fields.Char(string="Дизайн")
    link_chat = fields.Char(string="Чат")
    link_meeting = fields.Char(string="Встречи")

    # Связи (One2many)
    link_ids = fields.One2many("university.project.link", "project_id", string="Ссылки")
    document_ids = fields.One2many("university.project.document", "project_id", string="Документы")
    member_ids = fields.One2many("university.project.member", "project_id", string="Команда")

    project_owner_id = fields.Many2one("res.users", string="Владелец", default=lambda self: self.env.user)

    # --- ИСПРАВЛЕНИЕ: store=True обязательно для работы ir.rule и поисков ---
    member_user_ids = fields.Many2many(
        "res.users",
        compute="_compute_member_user_ids",
        string="Пользователи команды",
        store=True, 
    )

    @api.depends("member_ids.user_id", "project_owner_id")
    def _compute_member_user_ids(self):
        for project in self:
            members = project.member_ids.mapped("user_id")
            if project.project_owner_id:
                members |= project.project_owner_id
            project.member_user_ids = members


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Техническое поле для передачи списка участников в XML-вид
    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids", 
        string="Допустимые исполнители",
        readonly=True
    )

    # --- ГЛАВНАЯ ЗАЩИТА: Запрет на уровне сервера ---
    @api.constrains('user_ids', 'project_id')
    def _check_task_members(self):
        for task in self:
            # Если проект не установлен, пропускаем проверку
            if not task.project_id:
                continue
            
            # Если исполнители назначены
            if task.user_ids:
                # Находим тех, кто назначен, но кого нет в списке member_user_ids проекта
                invalid_users = task.user_ids - task.project_id.member_user_ids
                
                if invalid_users:
                    names = ", ".join(invalid_users.mapped('name'))
                    raise ValidationError(
                        f"Ошибка! Пользователи: [{names}] не являются участниками проекта '{task.project_id.name}'. "
                        "Вы не можете назначить задачу сотруднику вне команды."
                    )