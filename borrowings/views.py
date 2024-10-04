from django.utils.timezone import localdate
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    PermissionDenied,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)

from books.models import Book
from books.views import LibraryPagination
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingCreateSerializer,
    BorrowingUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        description="Retrieve a list of borrowings."
        "Non-admin users will only see their own borrowings.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter borrowings by active status."
                            "Use 'true' or 'false'.",
                required=False,
                examples=[
                    OpenApiExample("Active Borrowings", value="true"),
                    OpenApiExample("Inactive Borrowings", value="false"),
                ],
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter borrowings by user ID."
                            "Available only to admin users.",
                required=False,
            ),
        ],
        responses={200: BorrowingSerializer(many=True)},
    ),
    retrieve=extend_schema(
        description="Retrieve details of a borrowing by its ID."
                    "Non-admin users can only access their own borrowings.",
        responses={
            200: BorrowingSerializer,
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    ),
    create=extend_schema(
        description="Create a new borrowing."
                    "The user will be set"
                    "to the currently authenticated user.",
        request=BorrowingCreateSerializer,
        responses={
            201: BorrowingSerializer,
            400: OpenApiResponse(description="Validation Error"),
        },
    ),
    update=extend_schema(
        description="Update an existing borrowing."
                    "Only the owner of the borrowing can perform this action",
        request=BorrowingUpdateSerializer,
        responses={
            200: BorrowingSerializer,
            400: OpenApiResponse(description="Validation Error"),
            403: OpenApiResponse(description="Forbidden"),
        },
    ),
    partial_update=extend_schema(
        description="Partially update an existing borrowing."
                    "Only the owner of the borrowing can perform this action",
        request=BorrowingUpdateSerializer,
        responses={
            200: BorrowingSerializer,
            400: OpenApiResponse(description="Validation Error"),
            403: OpenApiResponse(description="Forbidden"),
        },
    ),
    destroy=extend_schema(
        description="Delete a borrowing."
                    "Only the owner of the borrowing can perform this action",
        responses={
            204: OpenApiResponse(description="No Content"),
            403: OpenApiResponse(description="Forbidden"),
        },
    ),
)
class BorrowingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing book borrowings.

    - Non-admin users can list, retrieve, update, and del their own borrowings
    - Admin users can access and manage all borrowings.
    - Users can create new borrowings.
    - Only the owner of a borrowing can update or delete it.
    """

    permission_classes = (IsAuthenticated,)
    queryset = Borrowing.objects.all()
    pagination_class = LibraryPagination

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action in ("update", "partial_update"):
            return BorrowingUpdateSerializer
        return BorrowingSerializer

    def get_object(self):
        obj = super().get_object()
        if not self.request.user.is_staff and obj.user != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this borrowing."
            )
        return obj

    def get_queryset(self):
        queryset = Borrowing.objects.all()
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        if is_active:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)
            else:
                raise DRFValidationError(
                    "Invalid value for is_active. Use 'true' or 'false'."
                )

        if not self.detail:
            if self.request.user.is_staff:
                if user_id:
                    queryset = queryset.filter(user_id=user_id)
            else:
                if user_id:
                    raise PermissionDenied(
                        "You do not have permission to filter by user_id."
                    )
                else:
                    queryset = queryset.filter(user=self.request.user)

        return queryset

    @extend_schema(
        description="Handle the creation of a new borrowing."
                    "Decreases the book's inventory if successful.",
        request=BorrowingCreateSerializer,
        responses={
            201: BorrowingSerializer,
            400: OpenApiResponse(description="Validation Error"),
        },
    )
    def perform_create(self, serializer):
        with transaction.atomic():
            book = serializer.validated_data["book"]
            book = Book.objects.select_for_update().get(pk=book.pk)

            if book.inventory <= 0:
                raise DRFValidationError(
                    {"book": "No more copies available to borrow."}
                )

            try:
                borrowing = serializer.save(user=self.request.user)
            except DjangoValidationError as e:
                raise DRFValidationError(detail=e.message_dict)

            try:
                book.borrow_book()
            except ValueError as e:
                borrowing.delete()
                raise DRFValidationError({"book": str(e)})

    @extend_schema(
        description=(
            "Handle the update of an existing borrowing. "
            "If 'manage_this_borrowing' is set to 'return',"
            "the borrowing is marked as returned."
        ),
        request=BorrowingUpdateSerializer,
        responses={
            200: BorrowingSerializer,
            400: OpenApiResponse(description="Validation Error"),
            403: OpenApiResponse(description="Forbidden"),
        },
    )
    def perform_update(self, serializer):
        borrowing = self.get_object()

        if self.request.user != borrowing.user:
            raise PermissionDenied(
                "You do not have permission to modify this borrowing."
            )

        if not borrowing.is_active:
            raise DRFValidationError(
                {"detail": "The book has already been returned."}
            )

        manage_this_borrowing = serializer.validated_data.get(
            "manage_this_borrowing"
        )

        if manage_this_borrowing == "return":
            serializer.save(actual_return_date=localdate())
            borrowing.book.return_book()
        else:
            serializer.save()

    @extend_schema(
        description="Delete an existing borrowing."
                    "Only the owner can perform this action.",
        responses={
            204: OpenApiResponse(description="No Content"),
            403: OpenApiResponse(description="Forbidden"),
        },
    )
    def perform_destroy(self, instance):
        if (
            not self.request.user.is_staff
            and instance.user != self.request.user
        ):
            raise PermissionDenied(
                "You do not have permission to delete this borrowing."
            )
        instance.delete()
