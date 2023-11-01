from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    title = models.CharField("Title", max_length=255)
    text = models.TextField("Text")
    date = models.DateTimeField(auto_now_add=True)
    html = models.BooleanField("Is the text HTML or plain text?", default=False)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Do we have to notify the users?
        # The object might not have an ID yet so it's new and then we want to notify the users
        should_notify = not self.id
        # Check before saving the actual object to check if it's new or not
        super().save(*args, **kwargs)
        if should_notify:
            users = User.objects.all()
            for user in users:
                new_blog = NewBlog(user=user, post=self)
                new_blog.save()


class NewBlog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="new_posts")

    def __str__(self):
        return f"{self.user} - {self.post}"
