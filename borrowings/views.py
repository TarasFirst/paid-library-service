from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing book borrowings.

    - This ViewSet allows creating, updating, deleting, and retrieving borrowings.
    - The `user` field is automatically assigned to the currently authenticated user when creating a borrowing.

    Methods:
    - `perform_create(self, serializer)`: Saves a new borrowing and associates it with the user.
      If validation errors occur, they are converted into Django REST Framework (DRF) validation errors.

    """
    permission_classes = (IsAuthenticated,)
    serializer_class = BorrowingSerializer
    queryset = Borrowing.objects.all()

    def get_queryset(self):
        queryset = Borrowing.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        if not self.request.user.is_staff:
            if self.request.query_params.get('user_id'):
                raise PermissionDenied("You do not have permission to filter by user_id.")
            return queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        """
        Creates a new borrowing entry, decreases the book inventory, and associates it with the current user.

        - Sets the `user` field to the currently authenticated user (`self.request.user`).
        - Calls the `borrow_book()` method on the selected book to decrease the inventory by 1.
        - Raises a `ValidationError` if the book's inventory is insufficient (inventory <= 0).
        - Handles model validation errors and converts them into DRF validation errors.

        Process:
        1. Retrieve the book from the validated data.
        2. Attempt to decrease the book's inventory by calling `borrow_book()`.
           If no copies are available, an error is raised.
        3. Save the borrowing entry with the current user assigned to the `user` field.

        Args:
            serializer: The serializer instance containing the data for the new borrowing.

        Raises:
            ValidationError:
                - If no copies of the book are available, a `ValueError` is raised by `borrow_book()`,
                  which is converted into a DRF `ValidationError`.
                - If any validation errors occur when saving the borrowing entry, they are converted into a DRF `ValidationError`.
        """
        book = serializer.validated_data["book"]
        try:
            book.borrow_book()
        except ValueError as e:
            raise DRFValidationError({"book": str(e)})

        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message_dict)
