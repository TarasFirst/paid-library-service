from django.test import TestCase

from books.models import Book


class BookInventoryTests(TestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.SOFT,
            inventory=5,
            daily_fee=1.99,
        )

    def test_borrow_with_zero_inventory_raises_error(self):
        """
        Test borrowing a book when inventory is zero raises a ValueError.
        """
        self.book.inventory = 0
        self.book.save()

        with self.assertRaises(ValueError):
            self.book.borrow_book()

    def test_return_book_without_borrowing(self):
        """
        Test returning a book without borrowing increases inventory.
        """
        initial_inventory = self.book.inventory
        self.book.return_book()
        self.assertEqual(self.book.inventory, initial_inventory + 1)

    def test_borrow_book_until_inventory_exhaustion(self):
        """
        Test borrowing books until inventory is zero prevents further borrowing.
        """
        for _ in range(self.book.inventory):
            self.book.borrow_book()

        self.assertEqual(self.book.inventory, 0)

        with self.assertRaises(ValueError):
            self.book.borrow_book()
