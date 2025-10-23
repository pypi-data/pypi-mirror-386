from dm_core.meta.decorator import api_inbound_validator
from django.conf import settings
from dm_core.tracer.decorator import trace_event_producer
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status


class CleanupApi(CreateAPIView):

    api_id = {
        'POST': f"{settings.SERVICE}.schedule.internal.cleanup"
    }

    def get_serializer_class(self):
        return None

    @api_inbound_validator()
    def post(self, request, *args, **kwargs):
        self.cleanup(data=None)
        return Response(status=status.HTTP_201_CREATED)

    @trace_event_producer()
    def cleanup(self, data, carrier):
        queue = settings.DM_REDIS_QUEUE
        queue.enqueue('processor.services.schedule.cleanup.cleanup_processor', data, carrier)
