from django.contrib import admin
from .models import Comment


# Register your models here.
class CommentModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'object_id', 'user', 'timestamp', 'content_type', 'content_object', 'content']

    class Meta:
        model = Comment

admin.site.register(Comment, CommentModelAdmin)
