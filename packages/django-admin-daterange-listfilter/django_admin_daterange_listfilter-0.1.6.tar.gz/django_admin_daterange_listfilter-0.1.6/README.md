# django-admin-daterange-listfilter

为Django模型列表页的时间过滤器增加日期范围选择功能。

## 使用方法

*settings.py*

```python
INSTALLED_APPS = [
    ...
    "django_static_jquery_ui",
    "django_middleware_global_request",
    "django_listfilter_media_extension",
    "django_admin_daterange_listfilter",
    ...
]
```

*admin.py*

```python
from django.contrib import admin
from django_admin_daterange_listfilter.filters import DateRangeFilter
from .models import Category


class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "add_time",
        "mod_time",
    ]
    list_filter = [
        ("add_time", DateRangeFilter),
        ("mod_time", DateRangeFilter),
    ]


admin.site.register(Category, CategoryAdmin)
```

## 版本记录

### v0.1.0

- 版本首发。

### v0.1.4

- 添加中文i18n翻译。

### v0.1.5

- 添加default_app_config以增强兼容性。

### v0.1.6

- Doc update.