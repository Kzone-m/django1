from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save   # right before the model is saved, we gonna do sth
from django.utils.text import slugify   # -> for creating Slug
from django.conf import settings    # -> for creating ForeignKey -> settings.AUTH_USER_MODEL
from django.utils import timezone

from markdown_deux import markdown
from django.utils.safestring import mark_safe

from comments.models import Comment
from django.contrib.contenttypes.models import ContentType

from .utils import get_read_time


"""
def upload_location(instance, filename):
    return "%s/%s" % (instance.id, filename)
    
    # This is an Alternative Way!!!
    # filebase, extention = filename.split('.')
    # return "%s/%s.%s" % (instance.id, instance.id, extention)
"""


# Post.objects.all()
# Post.objects.create(user=user, title='some')
class PostManager(models.Manager):
    # overriding original all method!!!
    def active(self, *args, **kwargs):
        return super(PostManager, self).filter(draft=False).filter(publish__lte=timezone.now())


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, default=1)   # default = 1 -> super admin user
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    # image = models.FileField(null=True, blank=True) -> default is noting, and it is not always required
    image = models.ImageField(  # -> this is a wat to show where image is actually uploaded to
            # upload_to=upload_location,
            null=True,
            blank=True,
            height_field='height_field',
            width_field='width_field'
        )
    height_field = models.IntegerField(default=0)
    width_field = models.IntegerField(default=0)
    content = models.TextField()
    draft = models.BooleanField(default=False)
    publish = models.DateField(auto_now=False, auto_now_add=False)
    read_time = models.TimeField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    objects = PostManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # return '/posts/%s/' %(self.id)
        # return reverse('posts:detail', kwargs={'slug': self.slug})
        return reverse('posts:detail', kwargs={'id': self.id})

    def get_markdown(self):
        content = self.content
        return mark_safe(markdown(content))

    @property
    def comments(self):
        instance = self
        qs = Comment.objects.filter_by_instance(instance)
        return qs

    @property
    def get_content_type(self):
        instance = self
        content_type = ContentType.objects.get_for_model(instance.__class__)
        return content_type

    class Meta:
        # noting does, but describe the class more
        ordering = ['-timestamp', '-updated']


def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Post.objects.filter(slug=slug).order_by('-id')
    exists = qs.exists()
    if exists:
        new_slug = '%s-%s' % (slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug


def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)

    if instance.content:
        html_string = instance.get_markdown()
        read_time_var = get_read_time(html_string)
        instance.read_time = read_time_var

pre_save.connect(pre_save_post_receiver, sender=Post)





