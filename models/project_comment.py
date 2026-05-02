# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class UniversityProjectComment(models.Model):
    _name = "university.project.comment"
    _description = "Project / Stage / Task Comment"
    _order = "create_date asc, id asc"

    task_id = fields.Many2one("project.task", string="Задача", ondelete="cascade", index=True)
    stage_id = fields.Many2one("university.project.stage", string="Этап", ondelete="cascade", index=True)

    author_id = fields.Many2one(
        "res.users",
        string="Автор",
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        ondelete="restrict",
    )
    create_date = fields.Datetime(string="Дата", readonly=True)
    message = fields.Html(string="Сообщение", sanitize=True)
    file_data = fields.Binary(string="Файл", attachment=True)
    file_name = fields.Char(string="Имя файла")

    @api.constrains("message", "file_data")
    def _check_payload(self):
        for rec in self:
            if not rec.message and not rec.file_data:
                raise ValidationError(_("Комментарий должен содержать текст или файл."))

    @api.constrains("task_id", "stage_id")
    def _check_parent(self):
        for rec in self:
            if not rec.task_id and not rec.stage_id:
                raise ValidationError(_("Комментарий должен быть привязан к задаче или этапу."))
            if rec.task_id and rec.stage_id:
                raise ValidationError(_("Комментарий не может быть привязан одновременно к задаче и этапу."))

    def _get_project(self):
        self.ensure_one()
        if self.task_id:
            return self.task_id.project_id
        if self.stage_id:
            return self.stage_id.project_id
        return self.env["project.project"]

    def _is_manager_or_admin(self, user):
        self.ensure_one()
        if user.has_group("project_management.administrator"):
            return True
        project = self._get_project()
        return project and user in project.project_manager_id

    def _can_create(self, user):
        self.ensure_one()
        if self._is_manager_or_admin(user):
            return True
        if self.task_id:
            return user in self.task_id.user_ids
        if self.stage_id:
            project = self.stage_id.project_id
            return project and user in project.member_user_ids
        return False

    def _can_edit(self, user):
        self.ensure_one()
        return self._is_manager_or_admin(user) or self.author_id == user

    @api.model_create_multi
    def create(self, vals_list):
        current_user = self.env.user
        prepared = []
        for vals in vals_list:
            vals = dict(vals)
            vals.setdefault("author_id", current_user.id)
            prepared.append(vals)
        records = super().create(prepared)
        for rec in records:
            if not rec._can_create(current_user):
                raise AccessError(_("У вас нет доступа для добавления комментария."))
        return records

    def write(self, vals):
        current_user = self.env.user
        for rec in self:
            if not rec._can_edit(current_user):
                raise AccessError(_("Редактировать комментарий может только автор, менеджер или администратор."))
        return super().write(vals)

    def unlink(self):
        current_user = self.env.user
        for rec in self:
            if not rec._can_edit(current_user):
                raise AccessError(_("Удалить комментарий может только автор, менеджер или администратор."))
        return super().unlink()
