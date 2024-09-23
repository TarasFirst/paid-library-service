from django.db import models

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")

    def __str__(self):
        return (f"{self.user.email} borrowed {self.book.title} from {self.borrow_date},"
                f"to {self.expected_return_date}")
