from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "HARD COVER", "HARD"
        SOFT = "SOFT COVER", "SOFT"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=10, choices=CoverType.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return (
            f"{self.title} ({self.author}),"
            f"cover: {self.cover}, price: {self.daily_fee} $ per day"
        )

    def borrow_book(self):
        """
        Decreases inventory by 1 when a book is borrowed.
        """
        if self.inventory > 0:
            self.inventory -= 1
            self.save()
        else:
            raise ValueError("No more copies available to borrow.")

    def return_book(self):
        """
        Increases inventory by 1 when a book is returned.
        """
        self.inventory += 1
        self.save()
