from django.contrib import admin

from .forms import CommentForm
from .models import Comment


class CommentAdminForm(admin.ModelAdmin):
    form = CommentForm
    readonly_fields = ("created_at",)


# Register your models here.
admin.site.register(Comment, CommentAdminForm)
