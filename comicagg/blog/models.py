# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

class Post(models.Model):
    user = models.ForeignKey(User)
    title = models.CharField('Título', max_length=255)
    text = models.TextField('Texto')
    date = models.DateTimeField(auto_now_add=True)
    html = models.BooleanField('Si se marca como HTML se pone a pelo en la web, si no, sólo los saltos de línea se convierten.', default=False)
    id_topic = models.IntegerField('Id del tema en el foro', null=True, blank=True, default=0, help_text='Se rellena él sólo')

    def __str__(self):
        return '%s' % self.title

    def save(self):
        #check if we have to notify the users
        notify = False
        if not self.id:
            notify = True
        super(Post, self).save()
        #avisar de que hay nuevo post
        if notify:
            users = User.objects.all()
            for user in users:
                new = NewBlog(user=user, post=self)
                new.save()

    class Meta:
        ordering = ['-date']

class NewBlog(models.Model):
    user = models.ForeignKey(User)
    post = models.ForeignKey(Post, related_name="new_posts")

    def __str__(self):
        return '%s - %s' % (self.user, self.post)

