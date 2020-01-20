from django.test import (
    SimpleTestCase as DjangoSimpleTestCase,
    TransactionTestCase as DjangoTransactionTestCase,
)

from celery_djangotest.base import CeleryUnitTestMixin


class SimpleTestCase(CeleryUnitTestMixin, DjangoSimpleTestCase):
    pass


class TransactionTestCase(CeleryUnitTestMixin, DjangoTransactionTestCase):
    pass
