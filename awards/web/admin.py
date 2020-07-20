from django.contrib import admin

from .models import Entry, Category, Rating


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_filter = ("category",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["__str__", "updated"]
