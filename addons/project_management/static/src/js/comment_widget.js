/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUpdateProps, markup } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { session } from "@web/session";

class CommentThreadWidget extends Component {
    static template = "project_management.CommentThread";
    static props = {
        ...standardFieldProps,
        context: { type: Object, optional: true },
        domain: { type: [Array, Function], optional: true },
        views: { type: Object, optional: true },
        relatedFields: { type: Object, optional: true },
        viewMode: { type: String, optional: true },
        widget: { type: String, optional: true },
        string: { type: String, optional: true },
        crudOptions: { type: Object, optional: true },
        addLabel: { type: String, optional: true },
        editable: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.currentUserId = session.uid;
        this.currentUserName = session.name;

        this.state = useState({
            comments: [],
            newMessage: "",
            fileName: "",
            fileData: null,
            submitting: false,
            loading: true,
        });

        onWillStart(() => this._loadComments());
        onWillUpdateProps(() => this._loadComments());
    }

    // ── определяем модель и parentId из props ──────────────────────────────
    get _parentField() {
        const ctx = this.props.record.context || {};
        if (ctx.default_task_id || this.props.record.resModel === "project.task") {
            return { field: "task_id", id: this.props.record.resId };
        }
        return { field: "stage_id", id: this.props.record.resId };
    }

    async _loadComments() {
        const { field, id } = this._parentField;
        if (!id) {
            this.state.comments = [];
            this.state.loading = false;
            return;
        }
        const rows = await this.orm.searchRead(
            "university.project.comment",
            [[field, "=", id]],
            ["author_id", "create_date", "message", "file_name", "file_data"],
            { order: "create_date asc, id asc" }
        );
        this.state.comments = rows;
        this.state.loading = false;
    }

    isOwn(comment) {
        return Number(comment.author_id?.[0]) === Number(this.currentUserId);
    }

    downloadUrl(comment) {
        return `/web/content?model=university.project.comment&id=${comment.id}&field=file_data&filename=${encodeURIComponent(comment.file_name || "file")}&download=true`;
    }

    avatarLetter(comment) {
        return (comment.author_id?.[1] || "?")[0].toUpperCase();
    }

    authorName(comment) {
        return comment.author_id?.[1] || "Неизвестно";
    }

    formatDate(dt) {
        if (!dt) return "";
        return new Date(dt).toLocaleString("ru-RU", {
            day: "2-digit", month: "2-digit", year: "numeric",
            hour: "2-digit", minute: "2-digit",
        });
    }

    messageHtml(comment) {
        return markup(comment.message || "");
    }

    onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) { this.state.fileName = ""; this.state.fileData = null; return; }
        this.state.fileName = file.name;
        const reader = new FileReader();
        reader.onload = (e) => { this.state.fileData = e.target.result.split(",")[1]; };
        reader.readAsDataURL(file);
    }

    clearFile() {
        this.state.fileName = "";
        this.state.fileData = null;
    }

    async onSubmit() {
        const msg = this.state.newMessage.trim();
        if (!msg && !this.state.fileData) return;
        if (this.state.submitting) return;
        this.state.submitting = true;
        try {
            const { field, id } = this._parentField;
            if (!id) return;
            await this.orm.create("university.project.comment", [{
                [field]: id,
                message: msg ? `<p>${msg}</p>` : false,
                file_data: this.state.fileData || false,
                file_name: this.state.fileName || false,
            }]);
            this.state.newMessage = "";
            this.state.fileData = null;
            this.state.fileName = "";
            await this._loadComments();
        } finally {
            this.state.submitting = false;
        }
    }

    async onDelete(comment) {
        await this.orm.unlink("university.project.comment", [comment.id]);
        await this._loadComments();
    }
}

registry.category("fields").add("comment_thread", {
    component: CommentThreadWidget,
    supportedTypes: ["one2many"],
});
