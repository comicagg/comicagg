# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

class Post(models.Model):
    user = models.ForeignKey(User)
    title = models.CharField('Title', max_length=255)
    text = models.TextField('Text')
    date = models.DateTimeField(auto_now_add=True)
    html = models.BooleanField('Is the text HTML or plain text?', default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return '%s' % self.title

    def save(self):
        # Do we have to notify the users
        notify = False
        if not self.id:
            # The object doesn't have an ID yet so it's new and then we want to notify the users
            notify = True
        super(Post, self).save()
        if notify:
            users = User.objects.all()
            for user in users:
                new = NewBlog(user=user, post=self)
                new.save()

class NewBlog(models.Model):
    user = models.ForeignKey(User)
    post = models.ForeignKey(Post, related_name="new_posts")

    def __str__(self):
        return '%s - %s' % (self.user, self.post)
