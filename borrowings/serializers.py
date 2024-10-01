from rest_framework import serializers

from books.models import Book
from borrowings.models import Borrowing
from books.serializers import BookDetailBorrowingSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    book_detail = BookDetailBorrowingSerializer(source="book", read_only=True)
    user = serializers.ReadOnlyField(source="user.email")
    borrow_date = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    actual_return_date = serializers.ReadOnlyField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "book_detail",
            "user",
            "is_active",
        ]


class BorrowingCreateSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.email")
    borrow_date = serializers.ReadOnlyField()
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    book_detail = BookDetailBorrowingSerializer(source="book", read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
            "book_detail",
            "user",
            "is_active",
        ]


class BorrowingUpdateSerializer(BorrowingSerializer):

    STATUS_CHOICES = [("keep", "Keep book"), ("return", "Return book")]
    manage_this_borrowing = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        default="keep",
        write_only=True,
    )
    user = serializers.ReadOnlyField(source="user.email")
    borrow_date = serializers.ReadOnlyField()
    expected_return_date = serializers.ReadOnlyField()
    book_detail = BookDetailBorrowingSerializer(source="book", read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_detail",
            "user",
            "manage_this_borrowing",
            "is_active",
        ]
