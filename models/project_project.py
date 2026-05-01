"""Extended Project Model
Main project model with team, documents, links, and tracking.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    """Extended project with university features"""
    _inherit = "project.project"
    _MANAGER_ROLE_CODE = "manager"           # used by _inverse (always creates with this role)
    _MANAGER_ROLE_CODES = ("manager", "project_lead")  # used by _compute (elevation)

    _TRANSITIONS_PM = {
        'draft':  {'active'},
        'active': {'done', 'cancel'},
    }
    _TRANSITIONS_ADMIN_ONLY = {
        'done':   {'active'},
        'cancel': {'active'},
    }

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
        default='draft',
        tracking=True,
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
        string='Заказчик',
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
        inverse="_inverse_project_manager_id",
        store=True,
        readonly=False
    )
    is_manager = fields.Boolean(
        compute="_compute_user_is_manager",
        string="Is current user a manager?",
        store=False
    )
    is_admin = fields.Boolean(
        compute="_compute_is_admin",
        store=False,
    )

    # ========== GENERAL INFO ==========
    division_id = fields.Many2one(
        'university.project.division',
        string='Подразделение',
        tracking=True,
    )
    division_code = fields.Char(
        string='Код подразделения',
        related='division_id.code',
        readonly=True,
        store=False,
    )
    division_name = fields.Char(
        string='Наименование подразделения',
        related='division_id.name',
        readonly=True,
        store=False,
    )
    contact_info = fields.Char(string='Контактная информация')
    budget = fields.Monetary(string='Бюджет', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Валюта',
        default=lambda self: self.env.ref('base.RUB', raise_if_not_found=False),
    )

    # ========== CLASSIFIERS ==========
    oecd_direction = fields.Char(string='Научное направление (OECD)')
    grnti_code = fields.Char(string='Код ГРНТИ')
    priority_ntr = fields.Text(
        string='Приоритетные направления НТР РФ',
    )
    critical_tech = fields.Text(string='Критические технологии')
    cross_tech = fields.Text(string='Сквозные технологии')
    big_challenges = fields.Text(string='Большие вызовы (СНТР РФ)')
    ntr_priorities = fields.Text(string='Приоритеты НТР РФ')
    national_projects = fields.Text(string='Мероприятия национальных проектов')
    keywords_ru = fields.Text(string='Ключевые слова (RU)')
    keywords_en = fields.Text(string='Keywords (EN)')

    # ========== DESCRIPTION ==========
    project_goal = fields.Html(string='Цель проекта')
    project_justification = fields.Html(string='Обоснование (потребности, проблемы, решения)')
    objective_ids = fields.One2many(
        'university.project.objective', 'project_id', string='Задачи проекта',
    )

    # ========== PARTNERS ==========
    partner_ids = fields.One2many(
        'university.project.partner', 'project_id', string='Партнёры',
    )

    # ========== RESULTS ==========
    trl_planned = fields.Many2one('university.project.trl', string='УГТ плановый', tracking=True)
    trl_actual = fields.Many2one('university.project.trl', string='УГТ фактический', tracking=True)
    trl_justification = fields.Text(string='Обоснование УГТ')
    result_ids = fields.One2many(
        'university.project.result', 'project_id', string='Результаты проекта',
    )
    result_requirement_ids = fields.One2many(
        'university.project.result', 'project_id', string='Требования к результатам',
    )
    indicator_ids = fields.One2many(
        'university.project.indicator', 'project_id', string='Показатели',
    )

    # ========== EFFECTS ==========
    effect_hse = fields.Html(string='Эффект на уровне НИУ ВШЭ')
    effect_industry = fields.Html(string='Эффект на отраслевом уровне')
    effect_rf = fields.Html(string='Эффект на уровне РФ')

    # ========== REQUIREMENTS ==========
    reporting_requirements = fields.Html(string='Требования к отчётности')
    other_requirements = fields.Html(string='Прочие требования')

    # ========== SIGNATORIES ==========
    signatory_ids = fields.One2many(
        'university.project.signatory', 'project_id', string='Подписанты',
    )

    # ========== PROJECT RELATIONS ==========
    predecessor_project_ids = fields.Many2many(
        'project.project',
        'project_predecessor_rel', 'project_id', 'predecessor_id',
        string='Проекты-предшественники',
    )
    customer_project_ids = fields.Many2many(
        'project.project',
        'project_customer_rel', 'project_id', 'customer_id',
        string='Проекты-заказчики',
    )
    executor_project_ids = fields.Many2many(
        'project.project',
        'project_executor_rel', 'project_id', 'executor_id',
        string='Проекты-исполнители',
    )
    competitor_project_ids = fields.Many2many(
        'project.project',
        'project_competitor_rel', 'project_id', 'competitor_id',
        string='Проекты-конкуренты',
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
        """Collect users with 'manager' or 'project_lead' role"""
        for project in self:
            managers = project.member_ids.filtered(
                lambda m: m.role_code in self._MANAGER_ROLE_CODES
            ).mapped('user_id')
            project.project_manager_id = managers

    def _inverse_project_manager_id(self):
        """Ensure selected managers are present in Team with manager role."""
        role_model = self.env["university.project.role"]
        member_model = self.env["university.project.member"]
        manager_role = role_model.search([("code", "=", self._MANAGER_ROLE_CODE)], limit=1)
        if not manager_role:
            raise ValidationError(
                _("Role with code '%s' is required for Project Manager sync.")
                % self._MANAGER_ROLE_CODE
            )

        for project in self:
            members_by_user = {member.user_id.id: member for member in project.member_ids}
            for user in project.project_manager_id:
                member = members_by_user.get(user.id)
                if not member:
                    member_model.create({
                        "project_id": project.id,
                        "user_id": user.id,
                        "role_id": manager_role.id,
                    })
                    continue
                if member.role_id != manager_role:
                    member.role_id = manager_role

    @api.depends_context('uid')
    def _compute_is_admin(self):
        is_admin = self.env.user.has_group('project_management.administrator')
        for project in self:
            project.is_admin = is_admin

    @api.depends('project_manager_id')
    @api.depends_context('uid')
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
        # 1. Create project(s) with standard Odoo flow.
        projects = super(Project, self).create(vals_list)
        
        # 2. Resolve default task stage templates by XML IDs.
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

        # 3. Assign default stage set to each created project.
        if stages:
            for project in projects:
                project.type_ids = [(6, 0, stages.ids)]
        
        return projects

    # ========== STATE MACHINE ==========
    def write(self, vals):
        if 'project_status' in vals:
            new_status = vals['project_status']
            is_admin = self.env.user.has_group('project_management.administrator')
            if not is_admin:
                labels = dict(self._fields['project_status'].selection)
                for rec in self:
                    old_status = rec.project_status
                    if old_status == new_status:
                        continue
                    allowed = self._TRANSITIONS_PM.get(old_status, set())
                    if new_status not in allowed:
                        raise UserError(_(
                            "Transition from '%(from)s' to '%(to)s' is not allowed.",
                            **{'from': labels.get(old_status, old_status),
                               'to': labels.get(new_status, new_status)}
                        ))
        return super().write(vals)

    # ========== VALIDATIONS ==========
    @api.constrains('project_date_start', 'project_date_end')
    def _check_dates(self):
        """Validate date constraints"""
        for project in self:
            if (project.project_date_start and project.project_date_end and
                    project.project_date_end < project.project_date_start):
                raise ValidationError(_("End Date cannot be earlier than Start Date."))

    # ========== ACTIONS ==========
    def action_start(self):
        return self.write({'project_status': 'active'})

    def action_done(self):
        return self.write({'project_status': 'done'})

    def action_cancel(self):
        return self.write({'project_status': 'cancel'})

    def action_resume(self):
        return self.write({'project_status': 'active'})

    def action_view_stages(self):
        """Open project stages"""
        self.ensure_one()
        list_view = self.env.ref('project_management.view_university_project_stage_list').id
        form_view = self.env.ref('project_management.view_university_project_stage_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Stages',
            'res_model': 'university.project.stage',
            'view_mode': 'list,form',
            'views': [
                (list_view, 'list'),
                (form_view, 'form'),
            ],
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
