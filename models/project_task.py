from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Project field mirrored from standard project_id for custom UI.
    projectID = fields.Many2one(
        'project.project',
        string="Проект",
        readonly=True,
        store=True,
        compute="_compute_project_id_custom",
        default=lambda self: self.env.context.get('default_project_id'),
    )

    # Dates
    date_start = fields.Date(string="Дата начала")
    date_end = fields.Date(string="Дата конца")

    # Task attachments
    document_ids = fields.One2many(
        "university.project.document",
        "task_id",
        string="Documents"
    )

    # Access helper: current user can edit if admin or project PM.
    is_manager = fields.Boolean(compute="_compute_is_manager")

    # University stage link
    university_stage_id = fields.Many2one(
        'university.project.stage',
        string="Этап проекта",
        tracking=True
    )

    # Allowed assignees filtered by project membership
    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids",
        string="Allowed Assignees",
        readonly=True
    )

    # Explicit priority field
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], default='0', string="Priority")

    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        ondelete='restrict',
        tracking=True,
        index=True,
        copy=False,
        group_expand='_read_group_stage_ids'
    )

    @api.depends('project_id')
    def _compute_project_id_custom(self):
        """Synchronize custom project field with standard Odoo project field."""
        for task in self:
            if task.project_id:
                task.projectID = task.project_id
            elif not task.projectID and self.env.context.get('default_project_id'):
                task.projectID = self.env.context.get('default_project_id')

    @api.depends('project_id')
    def _compute_is_manager(self):
        """Check if user can edit task (module admin or project PM)."""
        is_admin = self.env.user.has_group('project_management.administrator')

        for rec in self:
            is_project_manager = False
            if rec.project_id:
                is_project_manager = self.env.user in rec.project_id.project_manager_id
            rec.is_manager = is_admin or is_project_manager

    @api.constrains('date_end', 'university_stage_id')
    def _check_dates_against_stage(self):
        """Task end date cannot exceed related stage end date."""
        for task in self:
            if task.date_end and task.university_stage_id and task.university_stage_id.date_end:
                if task.date_end > task.university_stage_id.date_end:
                    raise ValidationError(
                        f"Дата конца задачи ({task.date_end}) не может быть позже "
                        f"даты конца этапа ({task.university_stage_id.date_end})"
                    )

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None, **kwargs):
        """Return kanban stages limited to the current project context."""
        project_id = self._context.get('default_project_id')

        if project_id:
            project = self.env['project.project'].browse(project_id)
            if project.exists() and project.type_ids:
                return project.type_ids

        return stages

    @api.model_create_multi
    def create(self, vals_list):
        """Allow task creation only for administrators or project PMs."""
        is_admin = self.env.user.has_group('project_management.administrator')

        if is_admin:
            return super().create(vals_list)

        for vals in vals_list:
            project_id = vals.get('project_id') or self.env.context.get('default_project_id')
            if not project_id:
                raise ValidationError(
                    "Task must be created from a project context or with project_id set."
                )

            project = self.env['project.project'].browse(project_id)
            if not project.exists() or self.env.user not in project.project_manager_id:
                raise ValidationError(
                    "Создавать задачи могут только администратор или PM выбранного проекта."
                )

        return super().create(vals_list)
