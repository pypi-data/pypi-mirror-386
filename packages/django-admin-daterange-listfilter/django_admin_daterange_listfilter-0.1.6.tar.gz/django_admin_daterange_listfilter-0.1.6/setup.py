# -*- coding: utf-8 -*-
import os
from io import open
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fobj:
    long_description = fobj.read()

with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as fobj:
    requires = [x.strip() for x in fobj.readlines() if x.strip()]

setup(
    name="django-admin-daterange-listfilter",
    version="0.1.6",
    description="为Django模型列表页的时间过滤器增加日期范围选择功能。",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Zhan YuCong",
    maintainer="Zhan YuCong",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=["django admin extentions", "daterange listfilter"],
    install_requires=requires,
    packages=find_packages(
        ".",
        exclude=[
            "django_admin_daterange_listfilter_demo",
            "django_admin_daterange_listfilter_example",
            "django_admin_daterange_listfilter_example.migrations",
        ],
    ),
    zip_safe=False,
    include_package_data=True,
)
