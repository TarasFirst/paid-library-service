from datetime import timedelta

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.timezone import localdate

from books.models import Book
from users.models import User
from borrowings.models import Borrowing


class BorrowingModelTest(TestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            inventory=5,
            cover=Book.CoverType.HARD,
            daily_fee=5.00,
        )
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

    def test_create_borrowing(self):
        """
        Test that a borrowing can be created with valid data.
        """
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=localdate() + timedelta(days=7),
        )
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.borrow_date, localdate())
        self.assertIsNone(borrowing.actual_return_date)

    def test_clean_method_validates_expected_return_date(self):
        """
        Test that clean() raises validation error
        if expected_return_date is in the past.
        """
        borrowing = Borrowing(
            book=self.book,
            user=self.user,
            expected_return_date=localdate() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError) as context:
            borrowing.clean()
        self.assertIn("Expected return date", context.exception.messages[0])

    def test_is_active_property(self):
        """
        Test that is_active property returns True
        if actual_return_date is None.
        """
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=localdate() + timedelta(days=7),
        )
        self.assertTrue(borrowing.is_active)

        borrowing.actual_return_date = localdate()
        borrowing.save()
        self.assertFalse(borrowing.is_active)

    def test_save_method_calls_clean(self):
        """
        Test that save() calls clean() before saving.
        """
        borrowing = Borrowing(
            book=self.book,
            user=self.user,
            expected_return_date=localdate() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            borrowing.save()

    def test_actual_return_date_can_be_saved_later(self):
        """
        Test that actual_return_date can be updated later
        without raising errors.
        """
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=localdate() + timedelta(days=7),
        )
        borrowing.actual_return_date = localdate()
        borrowing.save()
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, localdate())
