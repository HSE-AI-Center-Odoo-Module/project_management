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

        # Views
        "views/project_views.xml",
        "views/project_role_views.xml",
        "views/project_type_views.xml",
        "views/project_customer_views.xml",
        #'views/project_actions.xml',
    ],
    "application": True,
    "installable": True,
}
