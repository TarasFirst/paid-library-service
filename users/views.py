from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.serializers import UserSerializer

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)


@extend_schema(
    description="Create a new user account.",
    request=UserSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(description="Validation Error"),
    },
)
class CreateUserView(generics.CreateAPIView):
    """
    Endpoint for user registration.
    """
    serializer_class = UserSerializer


@extend_schema_view(
    get=extend_schema(
        description="Retrieve the authenticated user's details.",
        responses=UserSerializer,
    ),
    put=extend_schema(
        description="Update the authenticated user's details.",
        request=UserSerializer,
        responses=UserSerializer,
    ),
    patch=extend_schema(
        description="Partially update the authenticated user's details.",
        request=UserSerializer,
        responses=UserSerializer,
    ),
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for retrieving and updating the authenticated user's information.
    """
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
