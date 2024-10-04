from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book


class BookFilterTestCase(APITestCase):

    def setUp(self):
        self.book1 = Book.objects.create(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            cover="SOFT",
            inventory=5,
            daily_fee="1.00",
        )
        self.book2 = Book.objects.create(
            title="1984",
            author="George Orwell",
            cover="HARD",
            inventory=10,
            daily_fee="1.50",
        )
        self.book3 = Book.objects.create(
            title="To Kill a Mockingbird",
            author="Harper Lee",
            cover="SOFT",
            inventory=8,
            daily_fee="1.25",
        )
        self.books_list_url = reverse("books:book-list")

    def test_filter_books_by_title(self):
        response = self.client.get(self.books_list_url, {"title": "1984"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "1984")

    def test_filter_books_by_author(self):
        response = self.client.get(
            self.books_list_url, {"author": "Harper Lee"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["author"], "Harper Lee")

    def test_filter_books_by_title_and_author(self):
        response = self.client.get(
            self.books_list_url,
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["title"], "The Great Gatsby"
        )
        self.assertEqual(
            response.data["results"][0]["author"], "F. Scott Fitzgerald"
        )

    def test_filter_books_with_no_results(self):
        response = self.client.get(
            self.books_list_url, {"title": "Non-Existent Book"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_filter_books_without_query_params(self):
        response = self.client.get(self.books_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
