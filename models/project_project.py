"""Extended Project Model
Main project model with team, documents, links, and tracking.
"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Project(models.Model):
    """Extended project with university features"""
    _inherit = "project.project"

    # ========== METADATA ==========
    name_en = fields.Char(string="Project Name (EN)")
    project_status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
        ],
        string="Status",
        default='draft'
    )

    # ========== DATES ==========
    project_date_start = fields.Date(string="Start Date")
    project_date_end = fields.Date(string="End Date")
    date_error_msg = fields.Char(compute="_compute_date_error_msg")

    # ========== EXTERNAL LINKS ==========
    link_repo = fields.Char(string="Repository")
    link_docs = fields.Char(string="Documentation")
    link_design = fields.Char(string="Design")
    link_chat = fields.Char(string="Chat")
    link_meeting = fields.Char(string="Meetings")

    # ========== RELATIONS - REFERENCES ==========
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

    # ========== RELATIONS - TEAM ==========
    project_owner_id = fields.Many2one(
        "res.users",
        string="Project Owner",
        default=lambda self: self.env.user
    )
    member_ids = fields.One2many(
        "university.project.member",
        "project_id",
        string="Team"
    )
    member_user_ids = fields.Many2many(
        "res.users",
        compute="_compute_member_user_ids",
        string="Project Members",
        store=True
    )
    project_manager_id = fields.Many2many(
        'res.users',
        'project_project_managers_rel',
        'project_id', 'user_id',
        string='Project Manager',
        compute="_compute_project_manager_id",
        store=True,
        readonly=False
    )
    is_manager = fields.Boolean(
        compute="_compute_user_is_manager",
        string="Is current user a manager?",
        store=False
    )

    # ========== RELATIONS - CONTENT ==========
    link_ids = fields.One2many(
        "university.project.link",
        "project_id",
        string="Additional Links"
    )
    document_ids = fields.One2many(
        "university.project.document",
        "project_id",
        string="Documents"
    )

    # ========== COMPUTED FIELDS ==========
    @api.depends("member_ids.user_id", "project_owner_id")
    def _compute_member_user_ids(self):
        """Collect all member IDs including owner"""
        for project in self:
            members = project.member_ids.mapped("user_id")
            if project.project_owner_id:
                members |= project.project_owner_id
            project.member_user_ids = members

    @api.depends('member_ids.user_id', 'member_ids.role_id.code')
    def _compute_project_manager_id(self):
        """Collect users with 'manager' role"""
        for project in self:
            managers = project.member_ids.filtered(
                lambda m: m.role_id.code == 'manager'
            ).mapped('user_id')
            project.project_manager_id = managers

    @api.depends('project_manager_id')
    def _compute_user_is_manager(self):
        """Check if current user is manager"""
        is_admin = self.env.user.has_group('project_management.administrator')
        for project in self:
            project.is_manager = is_admin or (self.env.user in project.project_manager_id)

    @api.depends('project_date_start', 'project_date_end')
    def _compute_date_error_msg(self):
        """Validate date range"""
        for project in self:
            if (project.project_date_start and project.project_date_end and
                    project.project_date_end < project.project_date_start):
                project.date_error_msg = "Warning: End date cannot be earlier than start date!"
            else:
                project.date_error_msg = False

    @api.model_create_multi
    def create(self, vals_list):
        # 1. Ð¡Ð¾Ð·Ð´Ð°ÐµÐ¼ Ð¿Ñ€Ð¾ÐµÐºÑ‚ ÑÑ‚Ð°Ð½Ð´Ð°Ñ€Ñ‚Ð½Ñ‹Ð¼ ÑÐ¿Ð¾ÑÐ¾Ð±Ð¾Ð¼
        projects = super(Project, self).create(vals_list)
        
        # 2. ÐÐ°Ñ…Ð¾Ð´Ð¸Ð¼ Ð²Ð°ÑˆÐ¸ ÑÑ‚Ð°Ð¿Ñ‹ Ð¿Ð¾ Ð¸Ñ… Ð²Ð½ÐµÑˆÐ½Ð¸Ð¼ ID (Ð¸Ð· xml Ñ„Ð°Ð¹Ð»Ð°)
        # Ð£Ð±ÐµÐ´Ð¸Ñ‚ÐµÑÑŒ, Ñ‡Ñ‚Ð¾ 'project_management' â€” ÑÑ‚Ð¾ Ð¸Ð¼Ñ Ð¿Ð°Ð¿ÐºÐ¸ Ð²Ð°ÑˆÐµÐ³Ð¾ Ð¼Ð¾Ð´ÑƒÐ»Ñ
        stage_xml_ids = [
            'project_management.phase_backlog',
            'project_management.phase_spec',
            'project_management.phase_dev',
            'project_management.phase_test',
            'project_management.phase_delivered',
            'project_management.phase_archive',
        ]
        
        stages = self.env['project.task.type']
        for xml_id in stage_xml_ids:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                stages |= stage

        # 3. ÐŸÑ€Ð¸Ð²ÑÐ·Ñ‹Ð²Ð°ÐµÐ¼ ÑÑ‚Ð¸ ÑÑ‚Ð°Ð¿Ñ‹ Ðº ÐºÐ°Ð¶Ð´Ð¾Ð¼Ñƒ Ð½Ð¾Ð²Ð¾Ð¼Ñƒ ÑÐ¾Ð·Ð´Ð°Ð½Ð½Ð¾Ð¼Ñƒ Ð¿Ñ€Ð¾ÐµÐºÑ‚Ñƒ
        if stages:
            for project in projects:
                project.type_ids = [(6, 0, stages.ids)]
        
        return projects

    # ========== VALIDATIONS ==========
    @api.constrains('project_date_start', 'project_date_end')
    def _check_dates(self):
        """Validate date constraints"""
        for project in self:
            if (project.project_date_start and project.project_date_end and
                    project.project_date_end < project.project_date_start):
                raise ValidationError('End Date cannot be earlier than Start Date.')

    # ========== ACTIONS ==========
    def action_view_stages(self):
        """Open project stages"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Stages',
            'res_model': 'university.project.stage',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'create': self.is_manager,
            },
            'target': 'current',
        }

    def action_view_tasks(self):
        self.ensure_one()
        return self._build_task_board_action(
            project_id=self.id,
            action_name=f"Задачи: {self.name}",
        )

    def _task_board_domain(self, project_id):
        self.ensure_one()
        is_admin = self.env.user.has_group('project_management.administrator')
        is_project_manager = self.env.user in self.project_manager_id
        domain = [('project_id', '=', project_id)]
        if not (is_admin or is_project_manager):
            domain.append(('user_ids', 'in', self.env.user.id))
        return domain

    def _build_task_board_action(self, project_id, action_name):
        self.ensure_one()
        kanban_view = self.env.ref('project_management.view_university_task_kanban_custom').id
        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'res_model': 'project.task',
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': self._task_board_domain(project_id),
            'context': {
                'default_project_id': project_id,
                'group_by': 'stage_id',
                'active_test': False,
            },
            'target': 'current',
        }
