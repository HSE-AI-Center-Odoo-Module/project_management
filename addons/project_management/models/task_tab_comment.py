# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class UniversityTaskTabComment(models.Model):
    _name = "university.task.tab.comment"
    _description = "Task Tab Comment"
    _order = "create_date desc, id desc"

    tab_id = fields.Many2one("university.task.tab", string="Task Tab", required=True, ondelete="cascade")
    task_id = fields.Many2one(related="tab_id.task_id", string="Task", store=True, readonly=True)
    author_id = fields.Many2one(
        "res.users",
        string="Author",
        default=lambda self: self.env.user,
        readonly=True,
        ondelete="restrict",
    )
    message = fields.Html(string="Comment")
    file_data = fields.Binary(string="File")
    file_name = fields.Char(string="File Name")

    @api.constrains("message", "file_data")
    def _check_comment_payload(self):
        for rec in self:
            if not rec.message and not rec.file_data:
                raise ValidationError(_("Comment must contain text or file."))

    def _is_admin_or_manager(self, user):
        self.ensure_one()
        return bool(
            user.has_group("project_management.administrator")
            or user in self.tab_id.task_id.project_id.project_manager_id
        )

    def _can_user_create(self, user):
        self.ensure_one()
        return bool(
            self._is_admin_or_manager(user)
            or user in self.tab_id.task_id.user_ids
        )

    def _can_user_edit(self, user):
        self.ensure_one()
        return bool(
            self._is_admin_or_manager(user)
            or self.author_id == user
            or self.tab_id.responsible_id == user
        )

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = []
        current_user = self.env.user
        for vals in vals_list:
            vals = dict(vals)
            tab_id = vals.get("tab_id") or self.env.context.get("default_tab_id")
            tab = self.env["university.task.tab"].browse(tab_id).exists()
            if not tab:
                raise ValidationError(_("Task tab is required to create a comment."))

            pseudo_record = self.new({"tab_id": tab.id})
            if not pseudo_record._can_user_create(current_user):
                raise AccessError(_("Only task assignee, project manager, or administrator can add comments."))

            vals.setdefault("tab_id", tab.id)
            vals.setdefault("author_id", current_user.id)
            prepared_vals.append(vals)
        return super().create(prepared_vals)

    def write(self, vals):
        current_user = self.env.user
        for rec in self:
            if not rec._can_user_edit(current_user):
                raise AccessError(_("You cannot edit this comment."))
        return super().write(vals)

    def unlink(self):
        current_user = self.env.user
        for rec in self:
            if not rec._can_user_edit(current_user):
                raise AccessError(_("You cannot delete this comment."))
        return super().unlink()
