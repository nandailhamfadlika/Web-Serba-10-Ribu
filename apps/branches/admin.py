from django.contrib import admin
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'latitude', 'longitude', 'opening_hours', 'is_active')
    search_fields = ('name', 'address')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
