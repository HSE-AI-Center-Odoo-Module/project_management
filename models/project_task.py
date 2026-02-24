from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    date_start = fields.Date(string="Дата начала")
    date_end = fields.Date(string="Дата конца")

    document_ids = fields.One2many(
        "university.project.document",
        "task_id",
        string="Documents",
    )

    is_manager = fields.Boolean(compute="_compute_is_manager")

    university_stage_id = fields.Many2one(
        "university.project.stage",
        string="Этап проекта",
        tracking=True,
    )

    project_member_user_ids = fields.Many2many(
        related="project_id.member_user_ids",
        string="Allowed Assignees",
        readonly=True,
    )

    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        default="0",
        string="Priority",
    )

    stage_id = fields.Many2one(
        "project.task.type",
        string="Stage",
        ondelete="restrict",
        tracking=True,
        index=True,
        copy=False,
        group_expand="_read_group_stage_ids",
    )

    @api.depends("project_id")
    def _compute_is_manager(self):
        is_admin = self.env.user.has_group("project_management.administrator")
        for rec in self:
            is_project_manager = False
            if rec.project_id:
                is_project_manager = self.env.user in rec.project_id.project_manager_id
            rec.is_manager = is_admin or is_project_manager

    @api.constrains("date_end", "university_stage_id")
    def _check_dates_against_stage(self):
        for task in self:
            if task.date_end and task.university_stage_id and task.university_stage_id.date_end:
                if task.date_end > task.university_stage_id.date_end:
                    raise ValidationError(
                        f"Дата конца задачи ({task.date_end}) не может быть позже "
                        f"даты конца этапа ({task.university_stage_id.date_end})"
                    )

    @api.constrains("user_ids", "project_id")
    def _check_task_members(self):
        for task in self:
            if not task.project_id or not task.user_ids:
                continue
            invalid_users = task.user_ids - task.project_id.member_user_ids
            if invalid_users:
                names = ", ".join(invalid_users.mapped("name"))
                raise ValidationError(
                    f"Users: [{names}] are not members of project '{task.project_id.name}'."
                )

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None, **kwargs):
        project_id = self._context.get("default_project_id")
        if project_id:
            project = self.env["project.project"].browse(project_id)
            if project.exists() and project.type_ids:
                return project.type_ids
        return stages
