from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from requests.serializers.request_serializers import CreateRequestSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_request_view(request):
    serializer = CreateRequestSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        request_obj = serializer.save()
        return Response({'id': request_obj.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

