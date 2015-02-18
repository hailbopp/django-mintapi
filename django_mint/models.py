from __future__ import print_function

import datetime
import json
import mintapi
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models


class MintBody(models.Model):
    text = models.TextField()
    entity_type = models.CharField(max_length=128)


class MintModel(models.Model):
    source_body = models.ForeignKey(MintBody, null=True)

    class Meta:
        abstract = True


class MintUser(models.Model):
    username = models.CharField(max_length=512)
    password = models.CharField(max_length=512)  # Yes, this needs to be encrypted. Will handle in short order.

    django_user = models.ForeignKey(User, null=True)

    def perform_sync(self):
        mint = mintapi.Mint(self.username, self.password)

        accounts = mint.get_accounts(get_detail=True)
        print("Pulled %d accounts" % len(accounts))
        for account in accounts:
            #account_body = json.dumps(account)
            if not self.account_set.filter(mint_id=account['accountId']).exists():
                new_account = Account(mint_id=account['accountId'],
                                      account_type=account['accountType'],
                                      account_name=account['accountName'],
                                      long_name=account['fiLoginDisplayName'],
                                      currency=account['currency'],
                                      added_at=account['addAccountDateInDate'],
                                      owner=self)
                new_account.save()

            dj_account = self.account_set.filter(mint_id=account['accountId']).first()

            # TODO: maybe don't store a new historical balance if we already have one from the same update date
            new_balance = AccountBalance(account=dj_account,
                                         updated_at=account['lastUpdatedInDate'],
                                         balance=account['currentBalance'],
                                         current_interest_rate=account['interestRate'],
                                         )

            new_balance.current_account_limit = account.get('totalCredit', None)
            new_balance.current_interest_rate = account.get('interestRate', None)
            new_balance.next_due_date = account.get('dueDateInDate', None)
            new_balance.next_due_amount = account.get('dueAmt', None)

            new_balance.save()

            mint_transactions = mint.get_transactions(detailed=True, account_id=dj_account.mint_id)

            print("Got %d transactions for account %d" % (len(mint_transactions), dj_account.mint_id))

            for t in mint_transactions:
                if t['isPending']:
                    continue

                if not dj_account.transaction_set.filter(mint_id=t['id']).exists():
                    amount = Decimal(t['amount'].replace('$', '').replace(',', ''))
                    category, category_was_created = TransactionCategory.objects.get_or_create(owner=self, mint_id=t['categoryId'], defaults={'name': t['category']})
                    merchant, merchant_was_created = Merchant.objects.get_or_create(original_name=t['omerchant'], defaults={'name': t['merchant']})

                    dj_account.transaction_set.create(mint_id=t['id'], merchant=merchant, category=category, amount=amount,
                                                      date=t['dateInDate'],
                                                      is_check=t['isCheck'],
                                                      is_child=t['isChild'],
                                                      is_debit=t['isDebit'],
                                                      is_duplicate=t['isDuplicate'],
                                                      is_edited=t['isEdited'],
                                                      is_first_date=t['isFirstDate'],
                                                      is_linked_to_rule=t['isLinkedToRule'],
                                                      is_matched=t['isMatched'],
                                                      is_pending=t['isPending'],
                                                      is_spending=t['isSpending'],
                                                      is_transfer=t['isTransfer'],)


class Account(MintModel):
    mint_id = models.PositiveIntegerField()
    account_type = models.CharField(max_length=64)
    account_name = models.CharField(max_length=512)
    long_name = models.CharField(max_length=512)
    currency = models.CharField(max_length=128)
    added_at = models.DateTimeField()

    owner = models.ForeignKey(MintUser)

    @property
    def current_balance(self):
        return self.historical_balances.order_by('-updated_at').first()

    def __str__(self):
        balance = self.current_balance
        return "%s : %s : %f" % (self.account_name, self.account_type, balance.balance)


class AccountBalance(MintModel):
    account = models.ForeignKey(Account, related_name='historical_balances')
    retrieved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    balance = models.DecimalField(max_digits=20, decimal_places=2)
    current_interest_rate = models.DecimalField(max_digits=6, decimal_places=5, null=True)
    current_account_limit = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    next_due_date = models.DateTimeField(null=True)
    next_due_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)


class TransactionCategory(MintModel):
    name = models.CharField(max_length=512)
    mint_id = models.PositiveIntegerField()
    owner = models.ForeignKey(MintUser)


class Merchant(MintModel):
    name = models.CharField(max_length=512)
    original_name = models.CharField(max_length=512)


class Transaction(MintModel):
    mint_id = models.IntegerField()

    category = models.ForeignKey(TransactionCategory)
    merchant = models.ForeignKey(Merchant)
    account = models.ForeignKey(Account)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateTimeField()

    is_check = models.BooleanField(default=False)
    is_child = models.BooleanField(default=False)  # Child of what?
    is_debit = models.BooleanField(default=False)
    is_duplicate = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_first_date = models.BooleanField(default=False)  # Don't know what this one is. First date for what?
    is_linked_to_rule = models.BooleanField(default=False)  # TODO: Investigate links and rules
    is_matched = models.BooleanField(default=False)  # Matched to what?
    is_pending = models.BooleanField(default=False)
    is_spending = models.BooleanField(default=False)
    is_transfer = models.BooleanField(default=False)
