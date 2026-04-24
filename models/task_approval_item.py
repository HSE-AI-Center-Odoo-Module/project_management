# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class UniversityTaskApprovalItem(models.Model):
    _name = "university.task.approval.item"
    _description = "Task Approval Item"
    _order = "id"

    name = fields.Char(string="Checklist Item", required=True)
    task_id = fields.Many2one("project.task", string="Task", required=True, ondelete="cascade")
    responsible_id = fields.Many2one(
        "res.users",
        string="Approver",
        required=True,
        ondelete="restrict",
    )
    allowed_user_ids = fields.Many2many(
        related="task_id.project_id.member_user_ids",
        string="Allowed Users",
        readonly=True,
    )
    project_role_display = fields.Char(
        compute="_compute_project_role_display",
        string="Role in Project",
    )
    is_approved = fields.Boolean(string="Approved", default=False)
    approved_date = fields.Datetime(string="Approved On", readonly=True)
    note = fields.Html(string="Comment")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "university_task_approval_ir_attachment_rel",
        "approval_item_id",
        "attachment_id",
        string="Attachments",
    )
    comment_ids = fields.One2many(
        "university.task.approval.comment",
        "approval_item_id",
        string="Comments",
    )
    can_approve = fields.Boolean(compute="_compute_can_approve", string="Can Approve")
    can_revoke = fields.Boolean(compute="_compute_can_revoke", string="Can Revoke")

    @api.depends('responsible_id', 'task_id', 'task_id.project_id')
    def _compute_project_role_display(self):
        for rec in self:
            if rec.responsible_id and rec.task_id and rec.task_id.project_id:
                member = self.env['university.project.member'].search([
                    ('project_id', '=', rec.task_id.project_id.id),
                    ('user_id', '=', rec.responsible_id.id),
                ], limit=1)
                rec.project_role_display = member.role_id.name if member else ''
            else:
                rec.project_role_display = ''

    @api.depends("responsible_id", "task_id.project_id.project_manager_id", "is_approved")
    def _compute_can_approve(self):
        user = self.env.user
        is_admin = user.has_group("project_management.administrator")
        for rec in self:
            is_project_manager = bool(rec.task_id and user in rec.task_id.project_id.project_manager_id)
            rec.can_approve = bool(
                not rec.is_approved and (rec.responsible_id == user or is_project_manager or is_admin)
            )

    @api.depends("responsible_id", "task_id.project_id.project_manager_id", "is_approved")
    def _compute_can_revoke(self):
        user = self.env.user
        is_admin = user.has_group("project_management.administrator")
        for rec in self:
            is_project_manager = bool(rec.task_id and user in rec.task_id.project_id.project_manager_id)
            rec.can_revoke = bool(
                rec.is_approved and (rec.responsible_id == user or is_project_manager or is_admin)
            )

    def _can_user_edit_record(self, user):
        self.ensure_one()
        return bool(
            user.has_group("project_management.administrator")
            or user in self.task_id.project_id.project_manager_id
            or self.responsible_id == user
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
                raise ValidationError(_("Task and Responsible are required to create a checklist item."))
            vals.setdefault("task_id", task.id)
            is_project_manager = current_user in task.project_id.project_manager_id
            is_admin = current_user.has_group("project_management.administrator")
            if not (is_admin or is_project_manager or current_user == responsible):
                raise AccessError(
                    _("Only administrator, project manager, or responsible user can create a checklist item.")
                )
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
        current_user = self.env.user
        for rec in self:
            if not rec._can_user_edit_record(current_user):
                raise AccessError(
                    _("You cannot edit checklist item '%(item)s'. Only administrator, project manager, or responsible user can edit it.")
                    % {"item": rec.name}
                )
        if "is_approved" in vals:
            for rec in self:
                is_project_manager = current_user in rec.task_id.project_id.project_manager_id
                is_admin = current_user.has_group("project_management.administrator")
                if vals["is_approved"]:
                    if rec.responsible_id != current_user and not is_project_manager and not is_admin:
                        raise AccessError(
                            _("Only responsible approver '%(user)s' can approve item '%(item)s'.")
                            % {"user": rec.responsible_id.name, "item": rec.name}
                        )
                elif rec.responsible_id != current_user and not is_project_manager and not is_admin:
                    raise AccessError(_("You do not have access to revoke approval for '%(item)s'.") % {"item": rec.name})

            if vals["is_approved"]:
                vals.setdefault("approved_date", fields.Datetime.now())
            else:
                vals["approved_date"] = False

        protected_fields = {"name", "responsible_id", "note", "attachment_ids"}
        if protected_fields & set(vals.keys()):
            for rec in self:
                if not rec._can_user_edit_record(current_user):
                    raise AccessError(
                        _(
                            "You cannot edit checklist item '%(item)s'. Only administrator, project manager, or responsible user can edit it."
                        )
                        % {"item": rec.name}
                    )
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
        current_user = self.env.user
        for rec in self:
            if not rec._can_user_edit_record(current_user):
                raise AccessError(
                    _("You cannot delete checklist item '%(item)s'. Only administrator, project manager, or responsible user can delete it.")
                    % {"item": rec.name}
                )
        return super().unlink()

    def action_approve(self):
        for rec in self:
            if rec.responsible_id != self.env.user:
                raise AccessError(
                    _("Only '%(user)s' can approve checklist item '%(item)s'.")
                    % {"user": rec.responsible_id.name, "item": rec.name}
                )
            rec.write(
                {
                    "is_approved": True,
                    "approved_date": fields.Datetime.now(),
                }
            )
            rec.task_id.message_post(
                body=_("<b>%(user)s</b> approved checklist item <i>%(item)s</i>.")
                % {"user": self.env.user.name, "item": rec.name},
                message_type="notification",
            )

    def action_revoke(self):
        for rec in self:
            user = self.env.user
            is_project_manager = user in rec.task_id.project_id.project_manager_id
            is_admin = user.has_group("project_management.administrator")
            if rec.responsible_id != user and not is_project_manager and not is_admin:
                raise AccessError(_("You do not have access to revoke approval."))
            rec.write({"is_approved": False, "approved_date": False})
