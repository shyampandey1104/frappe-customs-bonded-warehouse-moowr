# Copyright (c) 2026, Shyamkumar Pandey and contributors
# For license information, please see license.txt

app_name = "customs_moowr"
app_title = "Frappe Customs Bonded Warehouse Moowr"
app_publisher = "Shyamkumar Pandey"
app_description = "Frappe Customs Bonded Warehouse Moowr - Enterprise Multi-DocType Solution for Frappe & ERPNext"
app_email = "shyampandey1104@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------
app_include_css = "/assets/customs_moowr/css/customs_moowr.bundle.css"
app_include_js = "/assets/customs_moowr/js/customs_moowr.bundle.js"

# Document Events
# ---------------
doc_events = {
    "Frappe Customs Bonded Warehouse Moowr Entry": {
        "validate": "customs_moowr.services.validator.EnterpriseValidationEngine.validate_compliance_rules",
        "on_submit": "customs_moowr.services.integration_service.EnterpriseIntegrationService.verify_remote_status"
    }
}

# Scheduled Background Tasks
# --------------------------
scheduler_events = {
    "hourly": [
        "customs_moowr.tasks.hourly_sync"
    ],
    "daily": [
        "customs_moowr.tasks.daily_reconciliation"
    ],
    "weekly": [
        "customs_moowr.tasks.weekly_digest"
    ]
}
