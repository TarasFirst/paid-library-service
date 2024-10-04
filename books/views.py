from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)

from books.models import Book
from books.serializers import BookListSerializer, BookDetailSerializer


class LibraryPagination(PageNumberPagination):
    page_size = 3
    max_page_size = 20


@extend_schema_view(
    list=extend_schema(
        description="Retrieve a list of all books.",
        responses=BookListSerializer,
    ),
    retrieve=extend_schema(
        description="Retrieve detailed information about a book by its ID.",
        responses=BookDetailSerializer,
    ),
    create=extend_schema(
        description="Create a new book. Accessible only to admin users.",
        request=BookDetailSerializer,
        responses=BookDetailSerializer,
    ),
    update=extend_schema(
        description="Update a book's information."
                    "Accessible only to admin users.",
        request=BookDetailSerializer,
        responses=BookDetailSerializer,
    ),
    partial_update=extend_schema(
        description="Partially update a book's information."
                    "Accessible only to admin users.",
        request=BookDetailSerializer,
        responses=BookDetailSerializer,
    ),
    destroy=extend_schema(
        description="Delete a book. Accessible only to admin users.",
        responses={204: None},
    ),
)
class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books.
    Allows performing standard CRUD operations on books.
    """

    queryset = Book.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LibraryPagination

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "retrieve",
        ):
            self.permission_classes = (IsAdminUser,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BookDetailSerializer

    def get_queryset(self):
        """Retrieve the book with filters"""
        title = self.request.query_params.get("title")
        author = self.request.query_params.get("author")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if author:
            queryset = queryset.filter(author__icontains=author)

        return queryset.distinct()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by book title " "(ex. ?title=fiction)",
            ),
            OpenApiParameter(
                "author",
                type=OpenApiTypes.STR,
                description="Filter by book author " "(ex. ?author=fiction)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
