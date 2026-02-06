from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Project(models.Model):
    _inherit = "project.project"

    # --- Ваши существующие поля ---
    name_en = fields.Char(string="Name (EN)")
    
    project_type_id = fields.Char(string='Type Name', required=True, translate=True)

    project_status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string="Status", default='draft')

    project_date_start = fields.Date(string="Start Date")
    project_date_end = fields.Date(string="End Date")
    date_error_msg = fields.Char(compute="_compute_date_error_msg")



    link_repo = fields.Char(string="Repository")
    link_docs = fields.Char(string="Documentation")
    link_design = fields.Char(string="Design")
    link_chat = fields.Char(string="Chat")
    link_meeting = fields.Char(string="Meetings")
    # Связи (One2many)
    link_ids = fields.One2many("university.project.link", "project_id", string="Additional Links")
    document_ids = fields.One2many("university.project.document", "project_id", string="Documents")
    member_ids = fields.One2many("university.project.member", "project_id", string="Team")

    project_owner_id = fields.Many2one("res.users", string="Project Owner", default=lambda self: self.env.user)

    # --- ИСПРАВЛЕНИЕ: store=True обязательно для работы ir.rule и поисков ---
    member_user_ids = fields.Many2many(
        "res.users",
        compute="_compute_member_user_ids",
        string="Project Members",
        store=True, 
    )

    @api.depends("member_ids.user_id", "project_owner_id")
    def _compute_member_user_ids(self):
        for project in self:
            members = project.member_ids.mapped("user_id")
            if project.project_owner_id:
                members |= project.project_owner_id
            project.member_user_ids = members

    project_manager_id = fields.Many2many(
        'res.users', 
        'project_project_managers_rel', # Имя таблицы связи (ОБЯЗАТЕЛЬНО)
        'project_id',                   # Колонка для проекта
        'user_id',                      # Колонка для пользователя
        string='Project Manager',
        tracking=True,
        help="Пользователь, обладающий правами менеджера для этого проекта"
    )

    is_manager = fields.Boolean(
        compute="_compute_user_is_manager",
        string="Is current user a manager?",
    )

    @api.depends('project_date_start', 'project_date_end')
    def _compute_date_error_msg(self):
        for project in self:
            if project.project_date_start and project.project_date_end and project.project_date_end < project.project_date_start:
                project.date_error_msg = "Внимание: Дата окончания не может быть раньше даты начала!"
            else:
                project.date_error_msg = False

    # Исправляем проверку менеджера (Many2many)
    @api.depends('project_manager_id')
    def _compute_user_is_manager(self):
        is_admin = self.env.user.has_group('project_management.administrator')
        for project in self:
            # Используем "in", так как это Many2many
            project.is_manager = is_admin or (self.env.user in project.project_manager_id)

    # Оставляем жесткую валидацию при сохранении
    @api.constrains('project_date_start', 'project_date_end')
    def _check_dates(self):
        for project in self:
            if project.project_date_start and project.project_date_end and project.project_date_end < project.project_date_start:
                raise ValidationError('End Date cannot be earlier than Start Date.')

    project_type_id = fields.Many2one(
        'university.project.type', 
        string='Project Type',
        tracking=True
    )
    
    custom_customer_id = fields.Many2one(
        'university.project.customer', 
        string='Customer',
        tracking=True
    )

class ProjectTask(models.Model):
    _inherit = "project.task"

    # Техническое поле для передачи списка участников в XML-вид
    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids", 
        string="Allowed Assignees",
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
                        f"Error! Users: [{names}] are not members of the project '{task.project_id.name}'. "
                        "You cannot assign a task to a user outside the project team."
                    )
                
    # ... ваши поля ...

    def action_view_tasks(self):
        """ Метод для открытия задач текущего проекта """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'list,form,kanban',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'target': 'current',
        }