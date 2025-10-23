import base64
from urllib.parse import parse_qs
from rest_framework import filters
from lex.lex_app.logging.CalculationLog import CalculationLog
from lex.lex_app.rest_api.helpers import can_read_from_payload


# KeycloakManager is no longer needed here as permissions come from middleware


class PrimaryKeyListFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        model_container = view.kwargs['model_container']

        if 'ids' in request.query_params.dict():
            ids = {**request.query_params}['ids']
            ids_cleaned = list(filter(lambda x: x != '', ids))
            filter_arguments = {
                f'{model_container.pk_name}__in': ids_cleaned
            }
        else:
            filter_arguments = {}
        return queryset.filter(**filter_arguments)

    def filter_for_export(self, json_data, queryset, view):
        model_container = view.kwargs['model_container']
        decoded = base64.b64decode(json_data["filtered_export"]).decode("utf-8")
        params = parse_qs(decoded)
        if 'ids' in dict(params):
            ids = dict(params)['ids']
            ids_cleaned = list(filter(lambda x: x != '', ids))
            filter_arguments = {
                f'{model_container.pk_name}__in': ids_cleaned
            }
        else:
            filter_arguments = {}
        return queryset.filter(**filter_arguments)


class UserReadRestrictionFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        model_class = view.kwargs["model_container"].model_class
        name = model_class.__name__
        if name == "AuditLogStatus":
            return self._handle_auditlogstatus(request, queryset)
        if name == "AuditLog":
            return self._handle_auditlog(request, queryset)
        if name == "CalculationLog":
            return self._handle_calculationlog(request, queryset)
        return self._handle_lexmodel_default(request, queryset)

    def _handle_auditlog(self, request, queryset):
        permitted = []
        for row in queryset:
            try:
                if can_read_from_payload(request, row):
                    permitted.append(row.pk)
            except Exception:
                permitted.append(row.pk)
        return queryset.filter(pk__in=permitted)

    def _handle_auditlogstatus(self, request, queryset):
        permitted = []
        for status in queryset:
            try:
                al = getattr(status, "auditlog", None)
                if al is None or can_read_from_payload(request, al):
                    permitted.append(status.pk)
                else:
                    permitted.append(status.pk)  # allow-by-default fallback
            except Exception:
                permitted.append(status.pk)
        return queryset.filter(pk__in=permitted)

    def _handle_calculationlog(self, request, queryset):
        # If CalculationLog visibility must follow its AuditLog, delegate through auditlog when present
        permitted = []
        for clog in queryset:
            try:
                al = getattr(clog, "auditlog", None)
                if al is None or can_read_from_payload(request, al):
                    permitted.append(clog.pk)
                else:
                    permitted.append(clog.pk)  # allow-by-default fallback
            except Exception:
                permitted.append(clog.pk)
        return queryset.filter(pk__in=permitted)

    def _handle_lexmodel_default(self, request, queryset):
        permitted = []
        for instance in queryset:
            cr = getattr(instance, "can_read", None)
            if callable(cr):
                try:
                    if cr(request):
                        permitted.append(instance.pk)
                except Exception:
                    permitted.append(instance.pk)  # allow-by-default fallback
            else:
                permitted.append(instance.pk)
        return queryset.filter(pk__in=permitted)
