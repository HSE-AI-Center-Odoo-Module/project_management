# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class UniversityTaskTab(models.Model):
    _name = "university.task.tab"
    _description = "Task Section"
    _order = "id"

    name = fields.Char(string="Section Name", required=True)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    responsible_id = fields.Many2one(
        "res.users",
        string="Responsible",
        required=True,
        ondelete="restrict",
    )
    allowed_user_ids = fields.Many2many(
        related="task_id.user_ids",
        string="Allowed Users",
        readonly=True,
    )
    content = fields.Html(string="Content", sanitize=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "university_task_tab_ir_attachment_rel",
        "tab_id",
        "attachment_id",
        string="Attachments",
    )
    comment_ids = fields.One2many(
        "university.task.tab.comment",
        "tab_id",
        string="Comments",
    )
    is_current_user_responsible = fields.Boolean(
        compute="_compute_is_current_user_responsible",
        string="Current User Can Edit Section",
    )

    @api.depends("responsible_id", "task_id.project_id.project_manager_id")
    def _compute_is_current_user_responsible(self):
        user = self.env.user
        is_admin = user.has_group("project_management.administrator")
        for rec in self:
            is_project_manager = bool(rec.task_id and user in rec.task_id.project_id.project_manager_id)
            rec.is_current_user_responsible = bool(
                is_admin or is_project_manager or rec.responsible_id == user
            )

    @api.constrains("responsible_id", "task_id")
    def _check_responsible_is_task_assignee(self):
        for rec in self:
            if rec.task_id and rec.responsible_id and rec.responsible_id not in rec.task_id.user_ids:
                raise ValidationError(
                    _("Responsible user '%(user)s' must be an assignee of task '%(task)s'.")
                    % {"user": rec.responsible_id.name, "task": rec.task_id.name}
                )

    def _can_user_edit_record(self, user):
        self.ensure_one()
        return bool(
            user.has_group("project_management.administrator")
            or user in self.task_id.project_id.project_manager_id
            or self.responsible_id == user
        )

    def _check_write_access(self):
        current_user = self.env.user
        for rec in self:
            if not rec._can_user_edit_record(current_user):
                raise AccessError(
                    _(
                        "Only responsible user '%(user)s', project manager, or administrator can edit section '%(section)s'."
                    )
                    % {"user": rec.responsible_id.name, "section": rec.name}
                )

    @api.model_create_multi
    def create(self, vals_list):
        records_to_create = []
        current_user = self.env.user
        for vals in vals_list:
            vals = dict(vals)
            task_id = vals.get("task_id") or self.env.context.get("default_task_id")
            task = self.env["project.task"].browse(task_id).exists()
            responsible = self.env["res.users"].browse(vals.get("responsible_id")).exists()
            if not task or not responsible:
                raise ValidationError(_("Task and Responsible are required to create a task tab."))
            vals.setdefault("task_id", task.id)
            is_project_manager = current_user in task.project_id.project_manager_id
            is_admin = current_user.has_group("project_management.administrator")
            if not (is_admin or is_project_manager or current_user == responsible):
                raise AccessError(_("Only administrator, project manager, or responsible user can create a tab."))
            records_to_create.append(vals)
        records = super().create(records_to_create)
        for rec in records:
            rec.attachment_ids.write(
                {
                    "res_model": rec._name,
                    "res_id": rec.id,
                }
            )
        return records

    def write(self, vals):
        protected_fields = {"content", "attachment_ids", "name", "responsible_id"}
        if protected_fields & set(vals.keys()):
            self._check_write_access()
        result = super().write(vals)
        if "attachment_ids" in vals:
            for rec in self:
                rec.attachment_ids.write(
                    {
                        "res_model": rec._name,
                        "res_id": rec.id,
                    }
                )
        return result

    def unlink(self):
        self._check_write_access()
        return super().unlink()
