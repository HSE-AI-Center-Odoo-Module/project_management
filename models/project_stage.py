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
        self.ensure_one()
        return self.project_id._build_task_board_action(
            project_id=self.project_id.id,
            action_name=f"Задачи: {self.name}",
        )

    # ========== METHODS ==========
    def write(self, vals):
        # Ð¡Ð¿Ð¸ÑÐ¾Ðº Ð¿Ð¾Ð»ÐµÐ¹, Ð¸Ð·Ð¼ÐµÐ½ÐµÐ½Ð¸Ñ ÐºÐ¾Ñ‚Ð¾Ñ€Ñ‹Ñ… Ð¼Ñ‹ Ñ…Ð¾Ñ‚Ð¸Ð¼ Ð»Ð¾Ð³Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ
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

                    # 1. ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚ÐºÐ° Ð¿Ð¾Ð»ÐµÐ¹ Selection (Ð¡Ñ‚Ð°Ñ‚ÑƒÑ)
                    if field == 'status':
                        selection = dict(self._fields['status'].selection)
                        old_val = selection.get(old_raw, old_raw)
                        new_val = selection.get(new_raw, new_raw)
                    
                    # 2. ÐžÐ±Ñ€Ð°Ð±Ð¾Ñ‚ÐºÐ° Many2one (ÐŸÑ€Ð¾ÐµÐºÑ‚)
                    elif field == 'project_id':
                        old_val = old_raw.display_name if old_raw else 'empty'
                        # Ð”Ð»Ñ Many2one Ð² vals Ð¿Ñ€Ð¸Ñ…Ð¾Ð´Ð¸Ñ‚ Ñ‚Ð¾Ð»ÑŒÐºÐ¾ ID (Ñ†Ð¸Ñ„Ñ€Ð°)
                        new_obj = self.env['project.project'].browse(new_raw)
                        new_val = new_obj.display_name if new_obj else 'empty'
                    
                    # 3. ÐžÑÑ‚Ð°Ð»ÑŒÐ½Ñ‹Ðµ Ð¿Ð¾Ð»Ñ (Char, Date)
                    else:
                        old_val = str(old_raw) if old_raw else 'empty'
                        new_val = str(new_raw) if new_raw else 'empty'

                    # Ð•ÑÐ»Ð¸ Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¸Ñ Ð´ÐµÐ¹ÑÑ‚Ð²Ð¸Ñ‚ÐµÐ»ÑŒÐ½Ð¾ Ð¸Ð·Ð¼ÐµÐ½Ð¸Ð»Ð¸ÑÑŒ
                    if str(old_raw) != str(new_raw):
                        changes.append(f"{label}: {old_val} â†’ {new_val}")

            # Ð•ÑÐ»Ð¸ Ð±Ñ‹Ð»Ð¸ Ð·Ð°Ñ„Ð¸ÐºÑÐ¸Ñ€Ð¾Ð²Ð°Ð½Ñ‹ Ð¸Ð·Ð¼ÐµÐ½ÐµÐ½Ð¸Ñ, ÑÐ¾Ð·Ð´Ð°ÐµÐ¼ Ð·Ð°Ð¿Ð¸ÑÑŒ Ð² Ð¸ÑÑ‚Ð¾Ñ€Ð¸Ð¸
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
