# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Post(models.Model):
  user = models.ForeignKey(User)
  title = models.CharField('Título', max_length=255)
  text = models.TextField('Texto')
  date = models.DateTimeField(auto_now_add=True)
  html = models.BooleanField('Si se marca como HTML se pone a pelo en la web, si no, sólo los saltos de línea se convierten.', default=False)
  id_topic = models.IntegerField('Id del tema en el foro', null=True, blank=True, default=0, help_text='Se rellena él sólo')

  def __unicode__(self):
    return u'%s' % self.title

  def save(self):
    notify = False
    if not self.id:
      notify = True
    super(Post, self).save()
    #avisar de que hay nuevo post
    if notify:
      users = User.objects.all()
      for user in users:
        try:
          up = user.get_profile()
          #up.last_read_access=datetime.now()
        except:
          up = UserProfile(user=user, last_read_access=datetime.now())
          #por cada usuario poner el campo del perfil new_comics a True
        if up.alert_new_blog:
          up.new_blogs = True;
          new = NewBlog(user=user, post=self)
          new.save()
          up.save()
      self.bot_post()

  def bot_post(self):
    import MySQLdb, time
    db = MySQLdb.connect(host='localhost', user=settings.DATABASE_USER, passwd=settings.DATABASE_PASSWORD, db='proyecto_accella', cursorclass=MySQLdb.cursors.DictCursor, use_unicode=True, charset='utf8')
    cursor = db.cursor()

    id_board = 16
    bot_id = 185
    bot_name = 'ComicAggregatorBot'
    bot_email = 'bot@comicagg.com'
    bot_ip = '0.0.0.0'
    timestamp = int(time.mktime(self.date.timetuple()))
    text = db.escape(self.text, db.encoders).decode('utf8').encode('ascii', 'xmlcharrefreplace')
    title = db.escape(self.title, db.encoders).decode('utf8').encode('ascii', 'xmlcharrefreplace')
    try:
      sql1 = u"""INSERT INTO `NSphere_topics` (`ID_TOPIC`, `isSticky`, `ID_BOARD`, `ID_FIRST_MSG`, `ID_LAST_MSG`, `ID_MEMBER_STARTED`, `ID_MEMBER_UPDATED`, `ID_POLL`, `numReplies`, `numViews`, `locked`) VALUES (NULL, 0, %d, 0, 0, %d, %d, 0, 0, 0, 0);""" % (id_board, bot_id, bot_id)
      cursor.execute(sql1)
      id_topic = db.insert_id()
      sql2 = u"""INSERT INTO `NSphere_messages` (`ID_MSG`, `ID_TOPIC`, `ID_BOARD`, `posterTime`, `ID_MEMBER`, `ID_MSG_MODIFIED`, `subject`, `posterName`, `posterEmail`, `posterIP`, `smileysEnabled`, `modifiedTime`, `modifiedName`, `body`, `icon`) VALUES (NULL, %d, %d, %d, %d, 0, %s, '%s', '%s', '%s', 0, 0, '', %s, 'xx');""" % (id_topic, id_board, timestamp, bot_id, title, bot_name, bot_email, bot_ip, text)
      cursor.execute(sql2)
      id_msg = db.insert_id()
      sql3 = u'UPDATE `NSphere_topics` SET `ID_FIRST_MSG` = %d, `ID_LAST_MSG` = %d WHERE `ID_TOPIC`=%d LIMIT 1;' % (id_msg, id_msg, id_topic)
      sql4 = u'UPDATE `NSphere_members` SET `posts` = `posts`+1 WHERE `NSphere_members`.`ID_MEMBER` =%d LIMIT 1;' % (bot_id)
      sql5 = u"UPDATE `NSphere_boards` SET `ID_LAST_MSG` = '%d', `ID_MSG_UPDATED` = '%d', numPosts = numPosts + 1, numTopics = numTopics + 1 WHERE `NSphere_boards`.`ID_BOARD` =%d LIMIT 1 ;" % (id_msg, id_msg, id_board)
      sql6 = u"UPDATE `NSphere_messages` SET ID_MSG_MODIFIED = %d WHERE ID_MSG = %d" % (id_msg, id_msg)
      cursor.execute(sql3)
      cursor.execute(sql4)
      cursor.execute(sql5)
      cursor.execute(sql6)
      self.id_topic = id_topic
      self.save()
    finally:
      db.close()

  class Meta:
    ordering = ['-date']

class NewBlog(models.Model):
  user = models.ForeignKey(User)
  post = models.ForeignKey(Post, related_name="new_posts")

  def __unicode__(self):
    return u'%s - %s' % (self.user, self.post)

