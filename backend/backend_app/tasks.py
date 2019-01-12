# -*- coding: utf-8 -*-
# ./backend_app/tasks.py
# Jie-Ting Jiang
import time
from celery import shared_task, current_task
from django.utils.timezone import now
from django.conf import settings
from .soundmaker import ArticleMeloday
from .crawler import PttCrawlerJob
from .models import TaskItem

# bind the task so that we can use self to access the task
@shared_task(bind=True)
def activate_spider(self, tid):
    # get the taskitem so we can update states into db in real-time
    task_record = TaskItem.objects.get(id=tid)
    # save celery's task id
    task_record.cel_taskid = self.request.id
    task_record.save()
    # if the task is not freshly initialized, it is not the task and sth must be wrong
    if task_record.state != 'initialized':
        current_task.update_state(
            state='ERROR',
            meta={'status': '0',
                'detail': "task has been executed..."})
    else:
        # state that AsyncResult(task_id).state will get
        current_task.update_state(
            state='PROGRESS',
            meta={'status': '0',
                'detail': "activating crawler..."})
        
        # TODO: consider if connection fails
        job = PttCrawlerJob(task_record.crawl_url)
        jobid = job.run()
        
        # update info
        task_record.hub_jobid = jobid
        task_record.save()

        # TODO: this part needs to be revised
        # TODO: what if suddenly lost connection with the api? this loop will never finish
        state = job.state
        while state != 'finished':
            time.sleep(10)
            job.update_meta()
            if state != job.state:
                state = job.state
                # TODO: update state to db
                task_record.state = state
                task_record.save()
                current_task.update_state(
                    state='PROGRESS',
                    meta={'status': '10',
                        'detail': "crawler is "+state})
        
        # get crawled items
        if job.item:
            item = job.item
            #print(item)
        else:
            # return error message
            raise AttributeError("Job has not item.")
        
        task_record.full_title = item[0]['title']
        task_record.board = item[0]['board']
        task_record.author = item[0]['author']

        current_task.update_state(
            state='PROGRESS',
            meta={'status': '50',
                'detail': "computing wave..."})
        
        # initialize ArticleMeloday
        am = ArticleMeloday(data=item)
        # preprocess data
        task_record.duration = am.preprocess()
        # make wave from comments
        am.make_comment_wave()
        
        current_task.update_state(
            state='PROGRESS',
            meta={'status': '90',
                'detail': "saving wave..."})
        
        # write freshly made wave file into media root
        am.write(filepath='%s/w_%s.wav'%(settings.WAV_MEDIA_ROOT, tid))
        
        # TODO: upload wave to user's soundcloud account
        # (but soundcloud api is currently unregisterable)

        current_task.update_state(
            state='PROGRESS',
            meta={'status': '100',
                'detail': "wave ready"})

        task_record.ended_dt = now()
        task_record.save()
