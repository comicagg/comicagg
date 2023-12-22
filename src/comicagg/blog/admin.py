from comicagg.blog.models import NewBlog, Post
from django.contrib import admin


class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "date",
        "user",
    )


class NewBlogAdmin(admin.ModelAdmin):
    ordering = (
        "user",
        "post",
    )


admin.site.register(Post, PostAdmin)
admin.site.register(NewBlog, NewBlogAdmin)
