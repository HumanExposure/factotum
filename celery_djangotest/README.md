# Celery Django Tests

A few tools to make testing in Django a bit easier when working with Celery.

## How it works

You have two options `celery_djangotest.unit` (unit tests) and `celery_djangotest.integration` (integration tests). Within each module are a `SimpleTestCase` and a `TransactionTestCase`. These act as drop-in replacements for Django's own test cases.

Both options will embed a Celery worker as a thread to your test process. This means you don't need to run a separate Celery worker instance to run your tests. In addition, each worker will listen on a separate queue so tests can be run in parallel. The database the worker uses will be the database Django uses in that test.

Unit tests use an in-memory broker and results store. In other words, you don't need to have a Celery app defined or any services available to use it. It is intended for testing reusable Django applications that make use of Celery.

Integration tests will use whatever Celery app you've defined in your Django application. It will use the broker and results store you've established in your Celery apps configuration. It is intended to test the full functionality of your application suite.

## How to use

```python
from celery_djangotest.unit import SimpleTestCase

class MyTest(SimpleTestCase):
    def test_something_using_celery(self):
        ...
```

## Runserver

It's possible to embed a live-updating Celery worker into Django's `runserver` using the same techniques employed to create these test cases. A context manager has been included to make this simple.

In `manage.py`

```python
def main():

    ...

    from celery_djangotest.utils import runserverwithcelery
    from myproj.celery import app

    with runserverwithcelery(app):
        execute_from_command_line(sys.argv)
```
