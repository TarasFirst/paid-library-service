from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from books.models import Book
from users.models import User


class BookViewSetPermissionsTest(APITestCase):

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

    def get_jwt_token(self, user):
        """
        Helper method to generate JWT tokens for a user
        """
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZE": f"Bearer {refresh.access_token}"}

    def test_unauthenticated_user_can_list_books(self):
        response = self.client.get(self.books_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_create_update_delete_books(self):
        data = {
            "title": "New Book",
            "author": "Author",
            "cover": "HARD",
            "inventory": 5,
            "daily_fee": "4.99",
        }
        response = self.client.post(self.books_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(self.book_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(self.book_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_non_admin_user_can_list_books(self):
        response = self.client.get(
            self.books_list_url, **self.get_jwt_token(self.user)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_non_admin_user_cannot_create_update_del_books(self):
        data = {
            "title": "New Book",
            "author": "Author",
            "cover": "HARD",
            "inventory": 5,
            "daily_fee": "4.99",
        }
        response = self.client.post(
            self.books_list_url, data, **self.get_jwt_token(self.user)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(
            self.book_detail_url, data, **self.get_jwt_token(self.user)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(
            self.book_detail_url, **self.get_jwt_token(self.user)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_admin_user_can_create_update_delete_books(self):
        data = {
            "title": "New Book",
            "author": "Author",
            "cover": "HARD",
            "inventory": 5,
            "daily_fee": "4.99",
        }

        response = self.client.post(
            self.books_list_url, data, **self.get_jwt_token(self.admin_user)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.put(
            self.book_detail_url, data, **self.get_jwt_token(self.admin_user)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(
            self.book_detail_url, **self.get_jwt_token(self.admin_user)
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_authenticated_non_admin_user_cannot_partial_update_book(self):
        data = {"title": "Updated Title"}
        response = self.client.patch(
            self.book_detail_url, data, **self.get_jwt_token(self.user)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_admin_user_can_partial_update_book(self):
        data = {"title": "Updated Title"}
        response = self.client.patch(
            self.book_detail_url, data, **self.get_jwt_token(self.admin_user)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_retrieve_book(self):
        response = self.client.get(self.book_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_non_admin_user_cannot_retrieve_book(self):
        response = self.client.get(
            self.book_detail_url, **self.get_jwt_token(self.user)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_create_book_with_invalid_data(self):
        data = {"title": ""}
        response = self.client.post(
            self.books_list_url, data, **self.get_jwt_token(self.admin_user)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
