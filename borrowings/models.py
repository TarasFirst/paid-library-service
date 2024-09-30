from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")

    @property
    def is_active(self):
        """
        Визначає, чи є бронювання активним. Якщо actual_return_date не встановлено,
        бронювання вважається активним.
        """
        return self.actual_return_date is None

    def __str__(self):
        return (f"{self.user.email} borrowed {self.book.title} from {self.borrow_date},"
                f"to {self.expected_return_date}")

    def clean(self):
        """Custom validation logic for expected_return_date and actual_return_date."""
        current_date = date.today()

        if self.expected_return_date < current_date:
            raise ValidationError(
                _("Expected return date %(expected)s cannot be earlier than today's date %(today)s"),
                params={"expected": self.expected_return_date, "today": current_date},
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
