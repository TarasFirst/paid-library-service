from rest_framework import serializers

from books.models import Book


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "cover", "inventory", "daily_fee"]


class BookDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "cover", "inventory", "daily_fee"]


class BookDetailBorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["title", "author", "cover", "daily_fee"]
