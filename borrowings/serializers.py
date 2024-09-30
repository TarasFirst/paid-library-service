from rest_framework import serializers

from books.models import Book
from borrowings.models import Borrowing
from books.serializers import BookDetailSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    book_detail = BookDetailSerializer(source="book", read_only=True)
    user = serializers.ReadOnlyField(source="user.email")
    borrow_date = serializers.ReadOnlyField()
    is_active = serializers.SerializerMethodField()

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
            "is_active"
        ]

    def get_is_active(self, obj):
        """
        Determines whether the borrowing is active (is_active).
        If actual_return_date is not set, the borrowing is active.
        """
        return obj.actual_return_date is None


class BorrowingCreateSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    user = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "expected_return_date",
            "book",
            "user",
        ]


class BorrowingUpdateSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.email")
    borrow_date = serializers.ReadOnlyField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "actual_return_date",
            "user",
            "borrow_date"
        ]
