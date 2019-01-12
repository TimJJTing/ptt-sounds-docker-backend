import os
import re
from redis import Redis
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings
from ptt_sounds.celery import app as celery_app
from .crawler import PttCrawlerJob
from .models import TaskItem

# Create your tests here.

class ScrapingHubTests(TestCase):
     def test_api_runnable(self):
         job = PttCrawlerJob(crawl_url='https://www.ptt.cc/bbs/Gossiping/M.1535039876.A.C9B.html')
         jobid = job.run()
         self.assertNotEquals(jobid, None)

class AsyncAvailablityTests(TestCase):
    def test_worker_is_standing_by(self):
        m = re.match(r"^[a-zA-Z]*?:\/\/(?P<host>[\w\.]*?):(?P<port>\d*?)\/\d*?$", settings.CELERY_BROKER_URL)
        broker_host = m.group('host')
        broker_port = m.group('port')
        bkr = Redis(host=broker_host, port=broker_port)
        # test if broker is standing by
        self.assertTrue(bkr.ping())
        # test if celery worker is standing by
        self.assertTrue(celery_app.control.inspect().active())

class MediaFileTests(TestCase):
    def test_media_wave_folder_exists(self):
        self.assertTrue(os.path.exists(settings.WAV_MEDIA_ROOT))

class TaskItemModelTests(TestCase):
    def setUp(self):
        self.item = TaskItem()
    def tearDown(self):
        self.item = None
    def test_non_ptt_url_not_allowed_1(self):
        self.item.crawl_url = 'https://www.ykk.cc/bbs/Gossiping/M.1535039876.A.C9B.html'
        self.item.save()
        self.assertRaisesMessage(
            expected_exception=ValidationError,
            expected_message='Not a PTT article url')

    def test_non_ptt_url_not_allowed_2(self):
        self.item.crawl_url = 'https://www.ptt.cc/M.1535039876.A.C9B'
        self.item.save()
        self.assertRaisesMessage(
            expected_exception=ValidationError,
            expected_message='Not a PTT article url')
