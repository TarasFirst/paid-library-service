from django.db import models


class Book(models.Model):
    HARD = "HARD"
    SOFT = "SOFT"
    COVER_CHOICES = [
        (HARD, "Hard Cover"),
        (SOFT, "Soft Cover"),
    ]

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=10, choices=COVER_CHOICES)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.title

    def borrow_book(self):
        """Decreases inventory by 1 when a book is borrowed."""
        if self.inventory > 0:
            self.inventory -= 1
            self.save()
        else:
            raise ValueError("No more copies available to borrow.")

    def return_book(self):
        """Increases inventory by 1 when a book is returned."""
        self.inventory += 1
        self.save()
