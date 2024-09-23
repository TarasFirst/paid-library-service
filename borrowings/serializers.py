from rest_framework import serializers

from borrowings.models import Borrowing
from books.serializers import BookDetailSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.email")
    book = BookDetailSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user"
        ]
