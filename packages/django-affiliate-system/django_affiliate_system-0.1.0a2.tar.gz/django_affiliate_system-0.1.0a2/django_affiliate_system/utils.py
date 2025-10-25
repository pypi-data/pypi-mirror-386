import csv

from django.apps import apps
from django.contrib import admin
from django.db.models import CharField, TextField
from django.http import HttpResponse

# from google.oauth2 import service_account
# from googleapiclient.discovery import build


# # === Google Calendar Webhook Setup ===
# SERVICE_ACCOUNT_FILE = "files/nextrole-464005-8b675d286f10.json"
# CALENDAR_ID = "tcpwebmaster9@gmail.com"  # Or your specific calendar ID
# WEBHOOK_URL = "https://c7eb-105-112-193-58.ngrok-free.app/webhooks/google-calendar/"  # Must be HTTPS!


# def setup_webhook():
#     credentials = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE,
#         scopes=["https://www.googleapis.com/auth/calendar"],
#     )

#     service = build("calendar", "v3", credentials=credentials)

#     channel = (
#         service.events()
#         .watch(
#             calendarId=CALENDAR_ID,
#             body={
#                 "id": "nextrole-channel-123aba3",
#                 "type": "web_hook",
#                 "address": WEBHOOK_URL,
#                 "params": {"ttl": "604800"},  # 7 days expiration
#             },
#         )
#         .execute()
#     )

#     print(f"Webhook set up! Channel ID: {channel['id']}")
#     print(f"Resource ID: {channel['resourceId']}")
#     # SAVE THESE TWO IDs - you'll need them later


# if __name__ == "__main__":
#     setup_webhook()


# === Django Admin Utilities ===
class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in self.exclude_fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected to CSV"


class AutoTableAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_per_page = 25
    exclude_fields = ["password", "last_login", "date_joined"]

    def __init__(self, model, admin_site):
        self.list_display = [
            field.name for field in model._meta.fields if field.name not in self.exclude_fields
        ]
        self.list_filter = [
            field.name
            for field in model._meta.fields
            if field.name not in self.exclude_fields and field.name != "id"
        ]
        self.search_fields = [
            field.name
            for field in model._meta.fields
            if field.name not in self.exclude_fields and isinstance(field, (CharField, TextField))
        ]
        super().__init__(model, admin_site)

    actions = ["export_as_csv"]


def auto_register_models(app_name, exclude_models=None, custom_admins=None):
    """
    Automatically register models with AutoTableAdmin.

    :param app_name: Name of the app to register models from
    :param exclude_models: List of model names to exclude from auto-registration
    :param custom_admins: Dictionary of model names and their custom admin classes
    """
    exclude_models = exclude_models or []
    custom_admins = custom_admins or {}

    app_models = apps.get_app_config(app_name).get_models()
    for model in app_models:
        if model.__name__ not in exclude_models:
            try:
                if model.__name__ in custom_admins:
                    admin.site.register(model, custom_admins[model.__name__])
                else:
                    admin.site.register(model, AutoTableAdmin)
            except admin.sites.AlreadyRegistered:
                pass
