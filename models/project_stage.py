"""Project Stage Model
Defines project stages/milestones with tracking.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class UniversityProjectStage(models.Model):
    """Project stage/milestone"""
    _name = 'university.project.stage'
    _description = 'Project Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'

    _TRANSITIONS_PM = {
        'draft':       {'in_progress', 'cancel'},
        'in_progress': {'done', 'cancel'},
        'cancel':      {'draft'},
    }

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
        compute="_compute_is_manager",
        store=False,
    )

    @api.depends('project_id', 'project_id.project_manager_id')
    @api.depends_context('uid', 'default_project_id')
    def _compute_is_manager(self):
        is_admin = self.env.user.has_group('project_management.administrator')
        for rec in self:
            project = rec.project_id
            if not project:
                ctx_pid = self.env.context.get('default_project_id')
                if ctx_pid:
                    project = self.env['project.project'].browse(ctx_pid)
            if is_admin:
                rec.is_manager = True
            elif project:
                rec.is_manager = self.env.user in project.project_manager_id
            else:
                rec.is_manager = False

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
                raise ValidationError(_("End Date cannot be earlier than Start Date."))

    # ========== ACTIONS ==========
    def action_start(self):
        return self.write({'status': 'in_progress'})

    def action_done(self):
        return self.write({'status': 'done'})

    def action_cancel(self):
        return self.write({'status': 'cancel'})

    def action_reset_to_draft(self):
        return self.write({'status': 'draft'})

    def action_view_tasks(self):
        self.ensure_one()
        return self.project_id._build_task_board_action(
            project_id=self.project_id.id,
            action_name=f"Задачи: {self.name}",
        )

    # ========== METHODS ==========
    def write(self, vals):
        # --- STATE MACHINE VALIDATION ---
        if 'status' in vals:
            new_status = vals['status']
            is_admin = self.env.user.has_group('project_management.administrator')
            if not is_admin:
                labels = dict(self._fields['status'].selection)
                for rec in self:
                    old_status = rec.status
                    if old_status == new_status:
                        continue
                    allowed = self._TRANSITIONS_PM.get(old_status, set())
                    if new_status not in allowed:
                        raise UserError(_(
                            "Transition from '%(from)s' to '%(to)s' is not allowed.",
                            **{'from': labels.get(old_status, old_status),
                               'to': labels.get(new_status, new_status)}
                        ))
            # --- APPROVAL GATE: status → done ---
            if new_status == 'done':
                for rec in self:
                    if rec.status == 'done':
                        continue
                    blocked = self.env['project.task'].search([
                        ('university_stage_id', '=', rec.id),
                        ('approval_count', '>', 0),
                    ]).filtered(lambda t: t.approval_done_count < t.approval_count)
                    if blocked:
                        raise UserError(_(
                            "Cannot complete stage '%(stage)s': %(count)d task(s) have unapproved items: %(tasks)s",
                            stage=rec.name,
                            count=len(blocked),
                            tasks=', '.join(blocked.mapped('name')),
                        ))

        # Track selected field changes in history.
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

                    # 1. Selection field handling.
                    if field == 'status':
                        selection = dict(self._fields['status'].selection)
                        old_val = selection.get(old_raw, old_raw)
                        new_val = selection.get(new_raw, new_raw)
                    
                    # 2. Many2one field handling.
                    elif field == 'project_id':
                        old_val = old_raw.display_name if old_raw else 'empty'
                        # For Many2one in vals we receive raw ID.
                        new_obj = self.env['project.project'].browse(new_raw)
                        new_val = new_obj.display_name if new_obj else 'empty'
                    
                    # 3. Other field types (Char/Date/etc.).
                    else:
                        old_val = str(old_raw) if old_raw else 'empty'
                        new_val = str(new_raw) if new_raw else 'empty'

                    # Log only real changes.
                    if str(old_raw) != str(new_raw):
                        changes.append(f"{label}: {old_val} -> {new_val}")

            # Persist history entry if there were changes.
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
