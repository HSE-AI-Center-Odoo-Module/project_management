from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Project(models.Model):
    _inherit = "project.project"

    # --- Информационные поля ---
    name_en = fields.Char(string="Project Name (EN)")
    
    project_status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string="Status", default='draft')

    project_date_start = fields.Date(string="Start Date")
    project_date_end = fields.Date(string="End Date")
    date_error_msg = fields.Char(compute="_compute_date_error_msg")

    # --- Ссылки и ресурсы ---
    link_repo = fields.Char(string="Repository")
    link_docs = fields.Char(string="Documentation")
    link_design = fields.Char(string="Design")
    link_chat = fields.Char(string="Chat")
    link_meeting = fields.Char(string="Meetings")
    
    link_ids = fields.One2many("university.project.link", "project_id", string="Additional Links")
    document_ids = fields.One2many("university.project.document", "project_id", string="Documents")
    
    # --- Команда и доступ ---
    member_ids = fields.One2many("university.project.member", "project_id", string="Team")
    project_owner_id = fields.Many2one("res.users", string="Project Owner", default=lambda self: self.env.user)

    # Список всех ID пользователей (членов команды) для Record Rules
    member_user_ids = fields.Many2many(
        "res.users",
        compute="_compute_member_user_ids",
        string="Project Members",
        store=True, 
    )

    # Менеджеры проекта (Вычисляемое поле)
    project_manager_id = fields.Many2many(
        'res.users', 
        'project_project_managers_rel', 
        'project_id', 'user_id',
        string='Project Manager',
        compute="_compute_project_manager_id",
        store=True, # Обязательно True для работы Record Rules в security.xml
        readonly=False,
        help="Пользователи с ролью 'Менеджер' в этом проекте"
    )

    is_manager = fields.Boolean(
        compute="_compute_user_is_manager",
        string="Is current user a manager?",
        store=False # Всегда вычислять для текущего сеанса
    )

    # --- Логика вычислений ---

    @api.depends("member_ids.user_id", "project_owner_id")
    def _compute_member_user_ids(self):
        for project in self:
            members = project.member_ids.mapped("user_id")
            if project.project_owner_id:
                members |= project.project_owner_id
            project.member_user_ids = members

    @api.depends('member_ids.user_id', 'member_ids.role_id.code')
    def _compute_project_manager_id(self):
        """Автоматически собирает менеджеров из вкладки Команда по коду роли 'manager'"""
        for project in self:
            # Ищем участников, у которых код роли равен 'manager'
            managers = project.member_ids.filtered(lambda m: m.role_id.code == 'manager').mapped('user_id')
            project.project_manager_id = managers

    @api.depends('project_manager_id')
    def _compute_user_is_manager(self):
        """Проверка прав текущего пользователя для интерфейса (readonly)"""
        is_admin = self.env.user.has_group('project_management.administrator')
        for project in self:
            project.is_manager = is_admin or (self.env.user in project.project_manager_id)

    @api.depends('project_date_start', 'project_date_end')
    def _compute_date_error_msg(self):
        for project in self:
            if project.project_date_start and project.project_date_end and project.project_date_end < project.project_date_start:
                project.date_error_msg = "Внимание: Дата окончания не может быть раньше даты начала!"
            else:
                project.date_error_msg = False

    # --- Валидация ---
    @api.constrains('project_date_start', 'project_date_end')
    def _check_dates(self):
        for project in self:
            if project.project_date_start and project.project_date_end and project.project_date_end < project.project_date_start:
                raise ValidationError('End Date cannot be earlier than Start Date.')

    # --- Связи с типами и заказчиками ---
    project_type_id = fields.Many2one('university.project.type', string='Project Type', tracking=True)
    custom_customer_id = fields.Many2one('university.project.customer', string='Customer', tracking=True)

    def action_view_stages(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Stages',
            'res_model': 'university.project.stage',
            'view_mode': 'list,form', # Сначала список, потом форма
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                # Ограничиваем возможность создания для не-менеджеров на уровне UI
                'create': self.is_manager, 
            },
            'target': 'current', # Открывает в текущем окне
        }

    def action_view_tasks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'kanban,form,list',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'target': 'current',
        }

class ProjectTask(models.Model):
    _inherit = "project.task"

    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids", 
        string="Allowed Assignees",
        readonly=True
    )

    @api.constrains('user_ids', 'project_id')
    def _check_task_members(self):
        for task in self:
            if not task.project_id:
                continue
            if task.user_ids:
                invalid_users = task.user_ids - task.project_id.member_user_ids
                if invalid_users:
                    names = ", ".join(invalid_users.mapped('name'))
                    raise ValidationError(
                        f"Users: [{names}] are not members of project '{task.project_id.name}'."
                    )