import datetime
from django.db import models


class MintBody(models.Model):
    text = models.TextField()
    entity_type = models.CharField()


class MintModel(models.Model):
    source_body = models.ForeignKey(MintBody)

    class Meta:
        abstract = True


class Account(MintModel):
    USAGE_TYPE_CHOICES = (
        ('PERSONAL', 'Personal'),
        ('BUSINESS', 'Business'),
        ('STUDENT', 'Student'),
        ('OTHER', 'Other')
    )

    mint_id = models.IntegerField()
    account_type = models.CharField(max_length=64)
    account_name = models.CharField(max_length=512)
    long_name = models.CharField(max_length=512)
    currency = models.CharField()
    added_at = models.DateTimeField()

    @property
    def current_balance(self):
        return self.historical_balances.order_by('-updated_at').first()


class AccountBalance(MintModel):
    account = models.ForeignKey(Account, related_name='historical_balances')
    updated_at = models.DateTimeField()

    balance = models.DecimalField(max_digits=20, decimal_places=2)
    current_interest_rate = models.DecimalField(max_digits=6, decimal_places=5)

    next_due_date = models.DateTimeField()
    next_due_amount = models.DecimalField(max_digits=20, decimal_places=2)


class TransactionCategory(MintModel):
    name = models.CharField(max_length=512)


class Merchant(MintModel):
    name = models.CharField(max_length=512)


class Transaction(MintModel):
    mint_id = models.IntegerField()

    category = models.ForeignKey(TransactionCategory)
    merchant = models.ForeignKey(Merchant)
    account = models.ForeignKey(Account)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateTimeField()

    is_check = models.BooleanField()
    is_child = models.BooleanField()                # Child of what?
    is_debit = models.BooleanField()
    is_duplicate = models.BooleanField()
    is_edited = models.BooleanField()
    is_first_date = models.BooleanField()           # Don't know what this one is. First date for what?
    is_linked_to_rule = models.BooleanField()       # TODO: Investigate links and rules
    is_matched = models.BooleanField()              # Matched to what?
    is_pending = models.BooleanField()
    is_spending = models.BooleanField()
    is_transfer = models.BooleanField()
