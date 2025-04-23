from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from ..models import CfcUser, ApprovedUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import logging
from ..serializers.account_serializers import LoginSerializer, SignupSerializer, LogoutSerializer
from django.db import transaction

logger = logging.getLogger(__name__)

def get_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f'Invalid request data: {serializer.errors}')
        return Response({'message': 'Invalid request data', 'errors': serializer.errors}, status=400)
    
    username = serializer.validated_data['username']
    if '@' in username:
        try:
            user = CfcUser.objects.get(email=username)
            username = user.username
        except CfcUser.DoesNotExist:
            logger.error(f'Unsuccessful login attempt for email {username}')
            return Response({'message': 'Invalid username or password'}, status=401)

    password = serializer.validated_data['password']
    logger.info(f'Login attempt for user {username}')
    user = authenticate(username=username, password=password)

    if user is None:
        return Response({'message': 'Invalid username or password'}, status=401)
    elif not user.is_active:
        return Response({'message': 'Your account is inactive. Please contact cousinsforcarol@gmail.com to reactivate'}, status=403)
    
    return Response({
        'message': 'Login successful',
        'tokens': get_token(user),
        'user': {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'job_title': user.job_title,
            'organization': user.organization,
            'admin_user': user.is_staff
            }
        },
        status=200
    )
        

@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def signup(request):
    serializer = SignupSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.error(f'Invalid request data: {serializer.errors}')
        return Response({'message': 'Invalid request', 'errors': serializer.errors}, status=400)
    
    email = serializer.validated_data['email']
    first_name = serializer.validated_data['first_name']
    last_name = serializer.validated_data['last_name']
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    job_title = serializer.validated_data['job_title']
    organization = serializer.validated_data['organization']
    
    logger.info(f'Signup request from {email} from {organization}')
    
    if not ApprovedUser.objects.filter(email=email).exists():
        logger.error(f'Sign up error: {email}')
        return Response({
            'message': 'You must be approved to sign up for our request portal.'
        }, status=403)

    if CfcUser.objects.filter(username=username).exists():
        logger.error(f'Username {username} already taken')
        return Response({'message': f'Username {username} is unavailable'}, status=400)
    
    if CfcUser.objects.filter(email=email).exists():
        logger.error(f'Email {email} is already in use')
        return Response({'message': 'The email you selected is already in use. Please log in'}, status=400)

    try:
        is_board_member = ApprovedUser.objects.get(email=email).is_staff
        user = CfcUser.objects.create_user(
            username=username, 
            first_name=first_name,
            last_name=last_name,
            password=password, 
            email=email, 
            job_title=job_title if not is_board_member else 'Board Member', 
            organization=organization if not is_board_member else 'Cousins For Carol', 
            is_staff=is_board_member
        )
    except Exception as e:
        logger.error(f'Error creating user {username} : {str(e)}')
        return Response({'message': 'Error creating user'}, status=500)
    
    ApprovedUser.objects.filter(email=email).update(signed_up=True)
    logger.info(f'{email} has signed up for the request portal!')
    return Response({
        'message': 'Signup successful',
        'tokens': get_token(user),
        'user': {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'job_title': user.job_title,
            'organization': user.organization,
            'admin_user': user.is_staff
            }
        },
        status=201
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'message': 'Invalid request data', 'errors': serializer.errors}, status=400)

        refresh_token = serializer.validated_data['refresh']
        if not refresh_token:
            return Response({'message': 'Refresh token required'}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'message': 'Invalid or expired token'}, status=400)

        return Response({'message': 'Successfully logged out'}, status=200)
    
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        return Response({'message': 'Unexpected error while logging out'}, status=500)
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_users(request):
    try:
        logger.info('Fetching list of users')
        users = CfcUser.objects.all()
        user_list = [
            {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'job_title': user.job_title,
                'organization': user.organization,
                'admin_user': user.is_staff
            }
            for user in users
        ]
        logger.info(f'Fetched {len(user_list)} users')
        if not user_list:
            return Response({'message': 'No users found'}, status=404)
        return Response(user_list, status=200)
    
    except Exception as e:
        logger.error(f'Error fetching users: {str(e)}')
        return Response({'message': 'Unexpected error while fetching users'}, status=500)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def add_user(request):
    try:
        email = request.query_params.get('email')
        if not email:
            return Response({'message': 'Email is required'}, status=400)

        if ApprovedUser.objects.filter(email=email).exists():
            return Response({'message': 'User already exists'}, status=400)

        ApprovedUser.objects.create(email=email)
        return Response({'message': 'User added successfully'}, status=201)
    
    except Exception as e:
        logger.error(f'Error adding user: {str(e)}')
        return Response({'message': 'Unexpected error while adding user'}, status=500)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def deactivate_user(request):
    try:
        email = request.query_params.get('email')
        if not email:
            return Response({'message': 'Email is required'}, status=400)
        try:
            user = CfcUser.objects.get(email=email)
            user.is_active = False
            user.save()
            return Response({'message': 'User deactivated successfully'}, status=200)
        except ApprovedUser.DoesNotExist:
            return Response({'message': 'User does not exist'}, status=404)
    
    except Exception as e:
        logger.error(f'Error deactivating user: {str(e)}')
        return Response({'message': 'Unexpected error while inactivating user'}, status=500)