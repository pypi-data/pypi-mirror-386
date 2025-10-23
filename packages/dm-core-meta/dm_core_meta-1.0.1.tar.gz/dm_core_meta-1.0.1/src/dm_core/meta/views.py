from rest_framework.generics import ListAPIView, UpdateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import exceptions
from django.conf import settings
from rq import Worker
from .decorator import api_inbound_validator
from .models import AppConfigModel
from .serializers import AppConfigSerializer


class AppConfigListApi(ListAPIView):

    api_id = {
        'GET': f"{settings.SERVICE}.meta.app-config.list"
    }
    serializer_class = AppConfigSerializer

    def get_queryset(self):
        return AppConfigModel.objects.all().order_by('key')

    @api_inbound_validator()
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AppConfigUpdateApi(ListAPIView):

    api_id = {
        'PUT': f"{settings.SERVICE}.meta.app-config.update"
    }
    serializer_class = AppConfigSerializer

    def get_input_serializer_instance(self):
        if self.request.method == 'PUT':
            instance_object = self.get_object()
            if instance_object is None:
                return None
            return self.serializer_class(instance=self.get_object(), data=self.request.data, partial=False)
        return None

    def get_object(self):
        try:
            return AppConfigModel.objects.get(key=self.kwargs.get('pk'))
        except AppConfigModel.DoesNotExist:
            return None

    @api_inbound_validator()
    def put(self, request, *args, **kwargs):
        serializer = kwargs.get('serializer')
        if serializer is None:
            raise exceptions.NotFound()
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('patch')



class VersionView(GenericAPIView):
    """
    VersionView: Display service and version information
    """
    api_id = {
        'GET': '{}.version'.format(settings.SERVICE)
    }

    def get(self, request):
        return Response({
            'service': settings.SERVICE,
            'workers': self.get_worker_count_for_queue()
        }, status=status.HTTP_200_OK)

    def get_worker_count_for_queue(self):
        workers = Worker.all(connection=settings.DM_REDIS_CONNECTION)
        target_queue_name = settings.DM_REDIS_QUEUE.name  # Extract only once

        def worker_has_target_queue(worker):
            try:
                return any(q.name == target_queue_name for q in worker.queues)
            except Exception as e:
                print(f"Warning: could not inspect queues for worker {worker.name}: {e}")
                return False

        return sum(1 for worker in workers if worker_has_target_queue(worker))