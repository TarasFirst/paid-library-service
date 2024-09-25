from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
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
    queryset = Borrowing.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = BorrowingSerializer

    def perform_create(self, serializer):
        """
        Creates a new borrowing entry and associates it with the current user.

        - Sets the `user` field to the currently authenticated user (`self.request.user`).
        - Handles model validation errors and converts them into DRF validation errors.

        Args:
            serializer: The serializer instance containing the data for the new borrowing.

        Raises:
            ValidationError: If validation errors occur, they are raised as DRF ValidationError.
        """
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message_dict)
