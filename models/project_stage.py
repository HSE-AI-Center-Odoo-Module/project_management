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
        """Open stage tasks"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'kanban,form,list',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
            'target': 'current',
        }


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

    # ========== METHODS ==========
    def write(self, vals):
        """Track status changes in history"""
        if 'status' in vals:
            for rec in self:
                self.env['university.project.stage.history'].create({
                    'stage_id': rec.id,
                    'name': f"Status changed from {rec.status} to {vals['status']}",
                })
        return super(UniversityProjectStage, self).write(vals)