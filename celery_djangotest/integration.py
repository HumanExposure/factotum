from django.test import (
    SimpleTestCase as DjangoSimpleTestCase,
    TransactionTestCase as DjangoTransactionTestCase,
)

from celery_djangotest.base import CeleryIntegrationTestMixin


class SimpleTestCase(CeleryIntegrationTestMixin, DjangoSimpleTestCase):
    pass


class TransactionTestCase(CeleryIntegrationTestMixin, DjangoTransactionTestCase):
    pass
