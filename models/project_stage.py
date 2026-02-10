"""Project Stage Model
Defines project stages/milestones with tracking.
"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UniversityProjectStage(models.Model):
    """Project stage/milestone"""
    _name = 'university.project.stage'
    _description = 'Project Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'

    # ========== BASIC FIELDS ==========
    name = fields.Char(
        string="Stage Name",
        required=True,
        tracking=True
    )
    description = fields.Html(string="Description")
    sequence = fields.Integer(default=10)

    # ========== STATUS & DATES ==========
    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('done', 'Completed'),
            ('cancel', 'Cancelled')
        ],
        string="Status",
        default='draft',
        tracking=True
    )
    date_start = fields.Date(string="Start Date", tracking=True)
    date_end = fields.Date(string="End Date", tracking=True)
    date_error_msg = fields.Char(compute="_compute_date_error_msg")

    # ========== RELATIONS ==========
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=True,
        ondelete='cascade'
    )
    document_ids = fields.One2many(
        "university.project.document",
        "stage_id",
        string="Documents"
    )
    history_ids = fields.One2many(
        'university.project.stage.history',
        'stage_id',
        string="History Log"
    )

    # ========== COMPUTED FIELDS ==========
    is_manager = fields.Boolean(
        related="project_id.is_manager",
        readonly=True
    )

    # ========== COMPUTED METHODS ==========
    @api.depends('date_start', 'date_end')
    def _compute_date_error_msg(self):
        """Validate date range"""
        for stage in self:
            if (stage.date_start and stage.date_end and
                    stage.date_end < stage.date_start):
                stage.date_error_msg = "Warning: End date cannot be earlier than start date!"
            else:
                stage.date_error_msg = False

    # ========== VALIDATIONS ==========
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Validate date constraints"""
        for stage in self:
            if (stage.date_start and stage.date_end and
                    stage.date_end < stage.date_start):
                raise ValidationError('End Date cannot be earlier than Start Date.')

    # ========== ACTIONS ==========
    def action_view_tasks(self):
        """Open tasks using custom kanban and form views"""
        self.ensure_one()
        
        # Получаем ID ваших новых представлений по их внешним ID (External ID)
        # Замените 'your_module_name' на реальное техническое имя вашего модуля
        kanban_view = self.env.ref('project_management.view_university_task_kanban_custom').id
        form_view = self.env.ref('project_management.view_university_task_form_custom').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Задачи: %s' % self.name,
            'res_model': 'project.task',
            # Указываем порядок переключения видов
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view, 'kanban'), # Первым откроется ваш кастомный канбан
                (False, 'list'),         # Список останется стандартным (False)
                (form_view, 'form'),     # При открытии задачи будет ваша новая форма
            ],
            # Если кнопка в проекте, используем self.id. Если в этапе — self.project_id.id
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {
                'default_project_id': self.project_id.id,
                # Группируем по стадиям (вашим фазам) сразу при открытии
                'group_by': 'stage_id',
            },
            'target': 'current',
        }

    
    # ========== METHODS ==========
    def write(self, vals):
        # Список полей, изменения которых мы хотим логировать
        tracked_fields = {
            'name': 'Name',
            'status': 'Status',
            'date_start': 'Start Date',
            'date_end': 'End Date',
            'project_id': 'Project'
        }

        for rec in self:
            changes = []
            for field, label in tracked_fields.items():
                if field in vals:
                    old_raw = rec[field]
                    new_raw = vals[field]

                    # 1. Обработка полей Selection (Статус)
                    if field == 'status':
                        selection = dict(self._fields['status'].selection)
                        old_val = selection.get(old_raw, old_raw)
                        new_val = selection.get(new_raw, new_raw)
                    
                    # 2. Обработка Many2one (Проект)
                    elif field == 'project_id':
                        old_val = old_raw.display_name if old_raw else 'empty'
                        # Для Many2one в vals приходит только ID (цифра)
                        new_obj = self.env['project.project'].browse(new_raw)
                        new_val = new_obj.display_name if new_obj else 'empty'
                    
                    # 3. Остальные поля (Char, Date)
                    else:
                        old_val = str(old_raw) if old_raw else 'empty'
                        new_val = str(new_raw) if new_raw else 'empty'

                    # Если значения действительно изменились
                    if str(old_raw) != str(new_raw):
                        changes.append(f"{label}: {old_val} → {new_val}")

            # Если были зафиксированы изменения, создаем запись в истории
            if changes:
                self.env['university.project.stage.history'].create({
                    'stage_id': rec.id,
                    'name': " | ".join(changes),
                    'user_id': self.env.user.id,
                    'date': fields.Datetime.now(),
                })

        return super(UniversityProjectStage, self).write(vals)


class UniversityProjectStageHistory(models.Model):
    """Stage change history log"""
    _name = 'university.project.stage.history'
    _description = 'Project Stage History'
    _order = 'date desc'

    # ========== RELATIONS ==========
    stage_id = fields.Many2one(
        'university.project.stage',
        string="Stage",
        ondelete='cascade'
    )

    # ========== FIELDS ==========
    name = fields.Char(string="Action", required=True)
    user_id = fields.Many2one(
        'res.users',
        string="User",
        default=lambda self: self.env.user
    )
    date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now
    )