"""
./backend_app/models.py
define models
"""
from django.db import models
from django.core.validators import RegexValidator

# Create your models here.
class TaskItem(models.Model):
    """
    Crawling task
    """
    STATE_CHOICES = (
        ('INI', 'initialized'),
        ('PEN', 'pending'),
        ('RUN', 'running'),
        ('FIN', 'finished'),
        ('ERR', 'error'),
    )
    cel_taskid = models.CharField(max_length=40, blank=True, null=True)
    hub_jobid = models.CharField(max_length=32, blank=True, null=True)
    crawl_url = models.URLField(
        max_length=70,
        validators=[
            RegexValidator(
                regex='^https:\/\/www\.ptt\.cc\/bbs\/[0-9A-Za-z_\-]{1,12}\/M\.\d{10}\.A\.[A-Z0-9]{3}\.html$',
                message='Not a PTT article url'
            )
        ]
    )
    created_dt = models.DateTimeField(auto_now_add=True)
    ended_dt = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=12, choices=STATE_CHOICES, default='initialized')
    full_title = models.CharField(max_length=70, blank=True, null=True)
    author = models.CharField(max_length=20, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    board = models.CharField(max_length=14, blank=True, null=True)
    
    def __str__(self):
        return '[%s] %s: %s'%(self.id, self.crawl_url, self.state)
    
    # Meta settings for db
    class Meta:
        db_table = "crawlTasks"
        