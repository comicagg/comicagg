from django.contrib import admin

from blog.models import NewBlog, Post


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
