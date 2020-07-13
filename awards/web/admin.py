from django.contrib import admin

from .models import Entry, Category


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_filter = ("category",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass
