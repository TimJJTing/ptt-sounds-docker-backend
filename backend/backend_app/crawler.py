from scrapinghub import ScrapinghubClient
from django.conf import settings

class PttCrawlerJob():
    def __init__(self, crawl_url):
        """ Initialize and build a connection with Scrapinghub via its api
        """
        self._client = ScrapinghubClient(settings.SCRAPINGHUB_APIKEY)
        # TODO: need to be revised
        self._project_id = self._client.projects.list()[0]
        self._project = self._client.get_project(self._project_id)
        self._target = crawl_url
        self._job = None
        self._meta = None
        self._state = 'initialized'
    
    def run(self):
        """ Run the crawler (spider)
        """
        if not self._job:
            self._job = self._project.jobs.run('ptt', job_args={'test_url': self._target})
            return self._job.key
        else:
            return None
    
    def update_meta(self):
        """ Update job's meta data
        """
        if self._job:
            self._meta = dict(self._job.metadata.iter())
            self._state = self._meta['state']
   
    def cancle(self):
        """ Cancle a job
        """
        self._job.cancel()

    @property
    def meta(self):
        """ Get job's meta data
        """
        if self._meta:
            return self._meta
        else:
            return None
    
    @property
    def state(self):
        """ Get job's current state
        """
        return self._state
    
    @property
    def item(self):
        """ Get scrapped items
        """
        if self._state == 'finished':
            # items.iter() returns a iterable, but is not a list and does not support indexing
            # so it has to be transformed into a list. Each element in the list is a dict.
            return list(self._job.items.iter())
        else:
            return None