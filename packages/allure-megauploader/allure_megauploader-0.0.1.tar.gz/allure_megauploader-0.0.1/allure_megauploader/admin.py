from django.contrib import admin

from allure_megauploader.models import ServiceType


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('verbose_name', 'service_code', 'description')
