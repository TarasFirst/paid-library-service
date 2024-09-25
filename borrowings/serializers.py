from rest_framework import serializers

from books.models import Book
from borrowings.models import Borrowing
from books.serializers import BookDetailSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    book_detail = BookDetailSerializer(source="book", read_only=True)
    user = serializers.ReadOnlyField(source="user.email")
    borrow_date = serializers.ReadOnlyField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
            "book_detail",
            "user",
        ]
