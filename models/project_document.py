# -*- coding: utf-8 -*-
"""Project Document Model."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class UniversityProjectDocument(models.Model):
    """Document attachment to projects, stages, and tasks."""

    _name = "university.project.document"
    _description = "Project Document Attachment"
    _order = "id desc"

    # ========== BASIC FIELDS ==========
    name = fields.Char(string="Description", required=True)

    # ========== FILE STORAGE ==========
    file_data = fields.Binary(string="File", required=True)
    file_name = fields.Char(string="File Name")

    # ========== AUDIT ==========
    uploaded_by = fields.Many2one(
        "res.users",
        string="Uploaded By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    uploaded_at = fields.Datetime(
        string="Uploaded At",
        default=fields.Datetime.now,
        readonly=True,
    )

    # ========== VERSIONING ==========
    version_of_id = fields.Many2one(
        "university.project.document",
        string="Version Of",
        ondelete="set null",
        help="Choose previous file to create next version.",
    )
    root_version_id = fields.Many2one(
        "university.project.document",
        string="Version Root",
        ondelete="cascade",
        readonly=True,
        index=True,
    )
    version_number = fields.Integer(string="Version", default=1, readonly=True)
    version_label = fields.Char(string="Version Label", compute="_compute_version_label")
    is_latest_version = fields.Boolean(string="Latest", compute="_compute_is_latest_version")
    version_ids = fields.One2many(
        "university.project.document",
        "version_of_id",
        string="Next Versions",
        readonly=True,
    )

    # ========== RELATIONS ==========
    project_id = fields.Many2one("project.project", string="Project", ondelete="cascade")
    stage_id = fields.Many2one("university.project.stage", string="Stage", ondelete="cascade")
    task_id = fields.Many2one("project.task", string="Task", ondelete="cascade")

    # ========== COMPUTES ==========
    @api.depends("version_number")
    def _compute_version_label(self):
        for doc in self:
            doc.version_label = f"v{doc.version_number}" if doc.version_number else False

    @api.depends("root_version_id", "version_number")
    def _compute_is_latest_version(self):
        for doc in self:
            if not doc.root_version_id:
                doc.is_latest_version = True
                continue
            latest = self.search(
                [("root_version_id", "=", doc.root_version_id.id)],
                order="version_number desc, id desc",
                limit=1,
            )
            doc.is_latest_version = bool(latest and latest.id == doc.id)

    # ========== ONCHANGE ==========
    @api.onchange("stage_id")
    def _onchange_stage_id(self):
        """Auto-fill project from selected stage."""
        if self.stage_id:
            self.project_id = self.stage_id.project_id

    # ========== CONSTRAINTS ==========
    @api.constrains("version_of_id", "project_id", "stage_id", "task_id")
    def _check_version_scope(self):
        for doc in self:
            if not doc.version_of_id:
                continue
            parent = doc.version_of_id
            if (
                parent.project_id != doc.project_id
                or parent.stage_id != doc.stage_id
                or parent.task_id != doc.task_id
            ):
                raise ValidationError(
                    _("Document version must belong to the same project/stage/task scope.")
                )

    # ========== ORM ==========
    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = []
        for vals in vals_list:
            vals = dict(vals)
            version_of_id = vals.get("version_of_id")

            if version_of_id:
                parent = self.browse(version_of_id).exists()
                if not parent:
                    raise ValidationError(_("Selected base document for versioning was not found."))

                vals.setdefault("project_id", parent.project_id.id)
                vals.setdefault("stage_id", parent.stage_id.id)
                vals.setdefault("task_id", parent.task_id.id)

                root_id = parent.root_version_id.id or parent.id
                vals["root_version_id"] = root_id

                latest = self.search(
                    [("root_version_id", "=", root_id)],
                    order="version_number desc, id desc",
                    limit=1,
                )
                vals["version_number"] = (latest.version_number if latest else 0) + 1
            else:
                vals.setdefault("version_number", 1)

            prepared_vals.append(vals)

        docs = super().create(prepared_vals)

        for doc in docs:
            if not doc.root_version_id:
                doc.root_version_id = doc.id

        return docs

    def action_create_new_version(self):
        """Open popup for creating next version of current file."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("New File Version"),
            "res_model": "university.project.document",
            "view_mode": "form",
            "view_id": self.env.ref("project_management.view_university_project_document_form").id,
            "target": "new",
            "context": {
                "default_name": self.name,
                "default_version_of_id": self.id,
                "default_project_id": self.project_id.id,
                "default_stage_id": self.stage_id.id,
                "default_task_id": self.task_id.id,
            },
        }
