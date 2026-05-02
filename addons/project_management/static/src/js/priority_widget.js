/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const LEVELS = [
    { value: "0", label: "Низкий",        cls: "pm-priority-low" },
    { value: "1", label: "Средний",       cls: "pm-priority-medium" },
    { value: "2", label: "Высокий",       cls: "pm-priority-high" },
    { value: "3", label: "Очень высокий", cls: "pm-priority-critical" },
];

class PriorityBadgeWidget extends Component {
    static template = "project_management.PriorityBadge";
    static props = { ...standardFieldProps };

    get current() {
        return LEVELS.find(l => l.value === this.props.record.data[this.props.name]) || LEVELS[0];
    }

    get levels() { return LEVELS; }

    onChange(ev) {
        this.props.record.update({ [this.props.name]: ev.target.value });
    }
}

registry.category("fields").add("priority_badge", {
    component: PriorityBadgeWidget,
    supportedTypes: ["selection"],
});
