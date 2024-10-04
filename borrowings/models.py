from django.core.exceptions import ValidationError
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from django.db import models

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField(default=localdate)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowings"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="borrowings"
    )

    @property
    def is_active(self):
        """
        Set - whether borrowing is active or not.
        """
        return self.actual_return_date is None

    def __str__(self):
        return (
            f"{self.user.email} borrowed {self.book.title}"
            f"from {self.borrow_date},"
            f"to {self.expected_return_date}"
        )

    def clean(self):
        """Custom validation logic for expected_return_date."""
        min_date = self.borrow_date or localdate()

        if self.expected_return_date < min_date:
            raise ValidationError(
                {
                    "expected_return_date": _(
                        "Expected return date %(expected)s"
                        "cannot be earlier than %(min_date)s"
                    )
                    % {
                        "expected": self.expected_return_date,
                        "min_date": min_date,
                    }
                }
            )

    def save(self, *args, **kwargs):
        if not self.borrow_date:
            self.borrow_date = localdate()
        self.full_clean()
        super().save(*args, **kwargs)
