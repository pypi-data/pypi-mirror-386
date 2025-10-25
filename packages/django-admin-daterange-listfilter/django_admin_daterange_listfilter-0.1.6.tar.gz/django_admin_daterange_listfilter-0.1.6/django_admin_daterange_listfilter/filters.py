import datetime
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import FieldListFilter


class DateRangeFilter(FieldListFilter):
    template = "django_admin_daterange_listfilter/filters/DateRangeFilter.html"

    def __init__(
        self,
        field,
        request,
        params,
        model,
        model_admin,
        field_path,
        input_start_placeholder=_("Date Start"),
        input_end_placeholder=_("Date End"),
    ):
        self.input_start_placeholder = input_start_placeholder
        self.input_end_placeholder = input_end_placeholder
        self.input_start_name = "{field_path}__gte".format(field_path=field_path)
        self.input_end_name = "{field_path}__lte".format(field_path=field_path)

        if self.input_start_name in params and params[self.input_start_name]:
            params[self.input_start_name] += " 00:00:00"
            params[self.input_start_name] = timezone.make_aware(
                datetime.datetime.strptime(
                    params[self.input_start_name], "%Y-%m-%d %H:%M:%S"
                )
            )

        if self.input_end_name in params and params[self.input_end_name]:
            params[self.input_end_name] += " 23:59:59"
            params[self.input_end_name] = timezone.make_aware(
                datetime.datetime.strptime(
                    params[self.input_end_name], "%Y-%m-%d %H:%M:%S"
                )
            )

        super().__init__(field, request, params, model, model_admin, field_path)

        if self.input_start_name in self.used_parameters:
            if not self.used_parameters[self.input_start_name]:
                del self.used_parameters[self.input_start_name]

        if self.input_end_name in self.used_parameters:
            if not self.used_parameters[self.input_end_name]:
                del self.used_parameters[self.input_end_name]

        self.input_start_value = self.used_parameters.get(self.input_start_name, "")
        if self.input_start_value:
            self.input_start_value = timezone.make_naive(
                self.input_start_value
            ).strftime("%Y-%m-%d")

        self.input_end_value = self.used_parameters.get(self.input_end_name, "")
        if self.input_end_value:
            self.input_end_value = timezone.make_naive(self.input_end_value).strftime(
                "%Y-%m-%d"
            )

    def expected_parameters(self):
        return [
            self.input_start_name,
            self.input_end_name,
        ]

    def choices(self, changelist):
        return []

    class Media:
        css = {
            "all": [
                "jquery-ui/jquery-ui.min.css",
                "django_admin_daterange_listfilter/css/DateRangeFilter.css",
            ]
        }
        js = [
            "admin/js/vendor/jquery/jquery.js",
            "jquery-ui/jquery-ui.min.js",
            "jquery-ui/i18n/datepicker-zh-Hans.js",
            "django_admin_daterange_listfilter/js/parseParam.js",
            "django_admin_daterange_listfilter/js/DateRangeFilter.js",
            "admin/js/jquery.init.js",
        ]
