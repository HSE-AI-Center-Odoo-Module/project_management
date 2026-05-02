# -*- coding: utf-8 -*-
{
    "name": "Project Management",
    "summary": "Project Management System for AI Research Centre HSE University",
    "category": "Project",
    "version": "18.0.0.1.0",
    "author": "Dandamaev Gadji",
    "license": "LGPL-3",
    "depends": [
                "base",
                "project", 
                "mail", 
    ],
    "data": [
        # Security
        "data/security_groups.xml",
        "security/ir.model.access.csv",
        "security/security.xml",

        # Data
        "data/project_role_data.xml",
        "data/russian_default.xml",
        "data/project_type_data.xml",
        "data/project_task_phases_data.xml",
        "data/project_trl_data.xml",

        # Views
        "views/project_division_views.xml",
        "views/project_trl_views.xml",
        "views/project_task_views.xml",
        "views/project_stage_views.xml",
        "views/project_views.xml",
        "views/project_role_views.xml",
        "views/project_type_views.xml",
        "views/project_customer_views.xml",
        "views/project_custom_views.xml",
        "views/project_users_view.xml",
        "views/project_stage_sync_wizard_views.xml",
        "views/project_document_views.xml",
        "views/employee_profile_views.xml",
        "views/menus.xml",

        # Setup — must be last (references actions and groups defined above)
        "data/admin_setup.xml",

    ],
    "assets": {
        "web.assets_backend": [
            "project_management/static/src/xml/chatter_templates.xml",
            "project_management/static/src/xml/comment_thread.xml",
            "project_management/static/src/xml/priority_widget.xml",
            "project_management/static/src/js/comment_widget.js",
            "project_management/static/src/js/priority_widget.js",
            "project_management/static/src/css/comment_thread.css",
        ],
    },
    "application": True,
    "installable": True,
}
