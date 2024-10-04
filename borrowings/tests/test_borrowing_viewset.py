from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import localdate
from rest_framework.test import APITestCase
from rest_framework import status

from books.models import Book
from borrowings.models import Borrowing
from users.models import User


class BorrowingViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password"
        )
        self.another_user = User.objects.create_user(
            email="another_user@example.com", password="password"
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )

        self.book_with_inventory = Book.objects.create(
            title="Available Book",
            author="Author",
            cover=Book.HARD,
            inventory=5,
            daily_fee="1.00",
        )
        self.book_no_inventory = Book.objects.create(
            title="Unavailable Book",
            author="Author",
            cover=Book.SOFT,
            inventory=0,
            daily_fee="1.50",
        )

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book_with_inventory,
            expected_return_date=localdate() + timedelta(days=7),
        )
        self.borrowing_completed = Borrowing.objects.create(
            user=self.user,
            book=self.book_with_inventory,
            borrow_date=localdate() - timedelta(days=14),
            expected_return_date=localdate() - timedelta(days=7),
            actual_return_date=localdate() - timedelta(days=1),
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_retrieve_borrowing_of_another_user(self):
        self.authenticate(self.another_user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to access this borrowing.",
        )

    def test_admin_can_retrieve_any_borrowing(self):
        self.authenticate(self.admin_user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.borrowing.id)

    def test_users_can_filter_own_borrowings_by_is_active(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-list") + "?is_active=true"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get("results", response.data)

        for item in results:
            self.assertTrue(item["is_active"])
            self.assertEqual(item["user"], self.user.email)

    def test_admin_can_filter_borrowings_by_user_id(self):
        self.authenticate(self.admin_user)
        url = reverse("borrowings:borrowing-list") + f"?user_id={self.user.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get("results", response.data)

        for item in results:
            self.assertEqual(item["user"], self.user.email)

    def test_users_cannot_filter_by_user_id(self):
        self.authenticate(self.user)
        url = (
            reverse("borrowings:borrowing-list")
            + f"?user_id={self.another_user.id}"
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to filter by user_id.",
        )

    def test_users_see_only_their_borrowings(self):
        self.authenticate(self.user)
        url = reverse("borrowings:borrowing-list")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get("results", response.data)

        for item in results:
            self.assertEqual(item["user"], self.user.email)

    def test_successful_borrowing_creation(self):
        self.authenticate(self.user)
        initial_inventory = self.book_with_inventory.inventory
        url = reverse("borrowings:borrowing-list")
        expected_return_date = localdate() + timedelta(days=7)

        response = self.client.post(
            url,
            {
                "book": self.book_with_inventory.id,
                "expected_return_date": expected_return_date.isoformat(),
            },
            format="json",
        )

        self.book_with_inventory.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            self.book_with_inventory.inventory, initial_inventory - 1
        )

    def test_inventory_not_decreased_on_invalid_borrowing_creation(self):
        self.authenticate(self.user)
        initial_inventory = self.book_with_inventory.inventory
        url = reverse("borrowings:borrowing-list")
        past_date = localdate() - timedelta(days=1)

        response = self.client.post(
            url,
            {
                "book": self.book_with_inventory.id,
                "expected_return_date": past_date.isoformat(),
            },
            format="json",
        )

        self.book_with_inventory.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.book_with_inventory.inventory, initial_inventory)

    def test_successful_return_book(self):
        self.authenticate(self.user)
        initial_inventory = self.book_with_inventory.inventory
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "return"}, format="json"
        )

        self.borrowing.refresh_from_db()
        self.book_with_inventory.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.borrowing.actual_return_date, localdate())
        self.assertEqual(
            self.book_with_inventory.inventory, initial_inventory + 1
        )
        self.assertFalse(self.borrowing.is_active)

    def test_cannot_update_completed_borrowing(self):
        self.authenticate(self.user)
        url = reverse(
            "borrowings:borrowing-detail", args=[self.borrowing_completed.id]
        )

        response = self.client.patch(
            url, {"manage_this_borrowing": "return"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "The book has already been returned.",
        )

    def test_update_without_changes_does_not_affect_borrowing(self):
        self.authenticate(self.user)
        initial_inventory = self.book_with_inventory.inventory
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "keep"}, format="json"
        )

        self.borrowing.refresh_from_db()
        self.book_with_inventory.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.borrowing.actual_return_date)
        self.assertEqual(self.book_with_inventory.inventory, initial_inventory)
        self.assertTrue(self.borrowing.is_active)

    def test_return_book_as_admin(self):
        self.authenticate(self.admin_user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])

        response = self.client.patch(
            url, {"manage_this_borrowing": "return"}, format="json"
        )

        self.borrowing.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to modify this borrowing.",
        )

    def test_parallel_borrowing_creation(self):
        self.authenticate(self.user)
        initial_inventory = self.book_with_inventory.inventory
        url = reverse("borrowings:borrowing-list")
        expected_return_date = localdate() + timedelta(days=7)

        response1 = self.client.post(
            url,
            {
                "book": self.book_with_inventory.id,
                "expected_return_date": expected_return_date.isoformat(),
            },
            format="json",
        )

        response2 = self.client.post(
            url,
            {
                "book": self.book_with_inventory.id,
                "expected_return_date": expected_return_date.isoformat(),
            },
            format="json",
        )

        self.book_with_inventory.refresh_from_db()

        self.assertTrue(
            (
                response1.status_code == status.HTTP_201_CREATED
                and response2.status_code == status.HTTP_201_CREATED
            )
            or (
                response1.status_code == status.HTTP_201_CREATED
                and response2.status_code == status.HTTP_400_BAD_REQUEST
            )
            or (
                response1.status_code == status.HTTP_400_BAD_REQUEST
                and response2.status_code == status.HTTP_201_CREATED
            )
        )

        expected_inventory = (
            initial_inventory
            - (1 if response1.status_code == status.HTTP_201_CREATED else 0)
            - (1 if response2.status_code == status.HTTP_201_CREATED else 0)
        )
        self.assertEqual(
            self.book_with_inventory.inventory, expected_inventory
        )

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
            {
                "book": self.book_with_inventory.id,
                "expected_return_date": past_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", response.data)
