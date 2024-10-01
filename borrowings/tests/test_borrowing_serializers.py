from datetime import date, timedelta

from django.urls import reverse
from django.utils.timezone import localdate
from rest_framework.test import APITestCase
from rest_framework import status

from books.models import Book
from borrowings.models import Borrowing
from users.models import User


class BorrowingAPITestCase(APITestCase):

    def setUp(self):
        # Створюємо користувачів
        self.user = User.objects.create_user(
            email="user@example.com", password="password"
        )
        self.another_user = User.objects.create_user(
            email="another_user@example.com", password="password"
        )

        # Створюємо книгу
        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            cover=Book.HARD,
            inventory=5,
            daily_fee="1.00",
        )

        # Створюємо активне бронювання
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=localdate() + timedelta(days=7),
        )

        borrow_date = localdate() - timedelta(days=14)
        expected_return_date = borrow_date + timedelta(days=7)
        actual_return_date = expected_return_date + timedelta(days=7)

        self.borrowing_completed = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=borrow_date,
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_successful_return_book(self):
        self.authenticate(self.user)
        initial_inventory = self.book.inventory
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "return"}, format="json"
        )

        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.borrowing.actual_return_date, localdate())
        self.assertEqual(self.book.inventory, initial_inventory + 1)
        self.assertFalse(self.borrowing.is_active)

    def test_return_book_by_another_user(self):
        self.authenticate(self.another_user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "return"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to access this borrowing.",
        )

    def test_update_completed_borrowing(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing_completed.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "return"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "The book has already been returned.",
        )

    def test_keep_book_no_changes(self):
        self.authenticate(self.user)
        initial_inventory = self.book.inventory
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "keep"}, format="json"
        )

        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, initial_inventory)
        self.assertTrue(self.borrowing.is_active)

    def test_invalid_manage_this_borrowing_value(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "invalid_option"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("manage_this_borrowing", response.data)

    def test_manage_this_borrowing_not_in_response(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("manage_this_borrowing", response.data)

    def test_cannot_update_readonly_fields(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        new_expected_return_date = localdate() + timedelta(days=30)
        new_borrow_date = localdate() - timedelta(days=5)

        response = self.client.patch(
            url,
            {
                "expected_return_date": new_expected_return_date.isoformat(),
                "borrow_date": new_borrow_date.isoformat(),
            },
            format="json",
        )

        self.borrowing.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(
            self.borrowing.expected_return_date, new_expected_return_date
        )
        self.assertNotEqual(self.borrowing.borrow_date, new_borrow_date)

    def test_create_borrowing_with_invalid_date(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-list")
        past_date = localdate() - timedelta(days=1)

        response = self.client.post(
            url,
            {"book": self.book.id, "expected_return_date": past_date.isoformat()},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", response.data)
