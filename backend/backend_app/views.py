"""
./backend_app/views.py
define views to render
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, Http404, HttpResponse
from celery.result import AsyncResult
from ptt_sounds.celery import app as celery_app
from .models import TaskItem
from .serializers import TaskItemSerializer
from .tasks import activate_spider

def index(request):
    """
    API hello world
    """
    return HttpResponse('<h1>Please specify your request.</h1>')

# Class-based views (CBV)
class TaskListView(APIView):
    """
    API endpoint that allows finished tasks to be viewed.
    List all tasks, or TODO: create a new task.
    """
    # A sentinel queryset required for DjangoModelPermissions
    queryset = TaskItem.objects.none()

    def get(self, request, *args, **kwargs):
        taskitem = TaskItem.objects.all().order_by('created_dt')
        serializer = TaskItemSerializer(taskitem, many=True, context={"request":request})
        return Response(serializer.data, status=200)

class TaskDetailView(APIView):
    """
    API endpoint that allows a finished task to be viewed in detail.
    Retrieve a task instance.
    """
    # A sentinel queryset required for DjangoModelPermissions
    queryset = TaskItem.objects.none()

    def get_object(self, pk):
        try:
            return TaskItem.objects.get(pk=pk)
        except TaskItem.DoesNotExist:
            raise Http404

    def get(self, request, pk, *args, **kwargs):
        taskitem = self.get_object(pk)
        serializer = TaskItemSerializer(taskitem, context={"request":request})
        return Response(serializer.data, status=200)

# function-based views (FBV)
# TODO: @ensure_csrf_cookie
@csrf_exempt
@require_http_methods(['POST']) # only post allowed
def schedule_task(request):
    """
    Schedule a new task.
    """
    if request.method == "POST":
        data = JSONParser().parse(request)
        # serialize
        serializer = TaskItemSerializer(data=data)
        # make sure redis is running first in the AsyncAvailablityTests, otherwise the next line will get stuck
        # if data is valid and celery app is running
        if serializer.is_valid() and celery_app.control.inspect().active():
            # save data into db
            serializer.save()
            # start the crawling task
            task = activate_spider.delay(serializer.instance.id)
            # if task is successfully scheduled
            if task:
                # return a success message. frontend show then request the task status
                return JsonResponse({
                    'id': serializer.instance.id,
                    'status': '0',
                    'detail': 'Task scheduled'
                })
            # else: sth wrong with celery
            return JsonResponse({
                'status': 'ERROR',
                'detail': 'Task scheduling error'
            })
            
        # else: data is not valid or celery is not running
        print('data is not valid or celery is not running')
        return JsonResponse({
            'status': 'ERROR',
            'detail': 'Input data is not valid or task scheduler is down'
        })

    # else: request method is not post
    return JsonResponse({
        'status': 'ERROR',
        'detail': 'Bad request'},
        status=400)

def current_task_status(request, tid, *args, **kwargs):
    """
    Get requests are for getting result of a specific crawling task.
    """
    if request.method == 'GET':
        # Here we check status of crawling that just started a few seconds ago.
        # If it is finished, we can query from database and get results
        # If it is not finished we can return active status
        # Possible results are -> pending, running, finished
        # receive a get request which contains /id/ as a TaskItem's id
        if tid:
            try:
                taskitem = TaskItem.objects.get(id=tid)
            except TaskItem.DoesNotExist:
                return JsonResponse({
                    'status': 'ERROR',
                    'detail': 'Requested item does not exist'})
            # get task's async result
            task = AsyncResult(taskitem.cel_taskid)
            # Note for task.result:
            # When the task has been executed, this contains the return value.
            # If the task raised an exception, this will be the exception instance.
            # In our case, whether a task is still running or finished successfully,
            # task.result will be None because we return nothing in the task,
            # but if the task raised an exception, this will be the exception instance.
            # task.state will be a progress rate or a 'SUCCESS' if finished.
            resp_data = task.result or task.state
            #print(resp_data)
            # if task.result returns an error, a task error occured.
            if isinstance(resp_data, Exception):
                return JsonResponse({
                    'status': 'ERROR',
                    'detail': 'Task error'})
            # if task is finished
            if resp_data == 'SUCCESS':
                return JsonResponse({
                    'status': '100',
                    'detail': 'Task finished'})
            # else: task is still running, return progress
            return JsonResponse(resp_data)
        # else: id not provided
        return JsonResponse({
            'status': 'ERROR',
            'detail': 'Must provide id'},
            status=400)
    # else: request method is not get
    return JsonResponse({
        'status': 'ERROR',
        'detail': 'Bad request'},
        status=400)
