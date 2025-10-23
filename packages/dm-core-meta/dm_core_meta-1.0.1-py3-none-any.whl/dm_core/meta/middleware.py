from django.http import JsonResponse
from dm_core.redis.service import cache_read
from rest_framework import status


class MaintenanceMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        if "/internal/" not in request.path and self.get_maintenance():
            return JsonResponse({'info': 'System under maintenance'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # If not in maintenance, continue with the next middleware or view
        response = self.get_response(request)
        return response

    @cache_read('maintenance')
    def get_maintenance(self, *args, **kwargs):
        """
        Return maintenance value from cache
        False if not found
        """
        is_maintenance = kwargs.get('cache_data')
        return False if is_maintenance is None else is_maintenance
