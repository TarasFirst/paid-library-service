from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from books.models import Book
from users.models import User


class BookSerializerCustomLogicTest(APITestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="SOFT",
            inventory=10,
            daily_fee="5.99",
        )

        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )

        self.admin_user = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )

        self.books_list_url = reverse("books:book-list")
        self.book_detail_url = reverse(
            "books:book-detail", kwargs={"pk": self.book.id}
        )

    def authenticate_client(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZE=f"Bearer {refresh.access_token}"
        )

    def test_list_action_uses_book_list_serializer(self):
        self.authenticate_client(self.user)
        response = self.client.get(self.books_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", [])
        expected_fields = [
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        ]

        for book in results:
            self.assertEqual(set(book.keys()), set(expected_fields))

    def test_retrieve_action_uses_book_detail_serializer(self):
        self.authenticate_client(self.admin_user)
        response = self.client.get(self.book_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = [
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        ]
        self.assertEqual(set(response.data.keys()), set(expected_fields))

    def test_create_action_uses_book_detail_serializer(self):
        self.authenticate_client(self.admin_user)
        data = {
            "title": "Admin Book",
            "author": "Admin Author",
            "cover": "HARD COVER",
            "inventory": 5,
            "daily_fee": "9.99",
        }
        response = self.client.post(self.books_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_fields = [
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        ]
        self.assertEqual(set(response.data.keys()), set(expected_fields))
