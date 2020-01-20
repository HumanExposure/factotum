# Celery Form Task

Turn a Django form into a Celery task.

## How it works

This mixin will add an extra command to your form: `enqueue()`. Executing this will setup a Celery task to process the `clean()` and `save()` methods of your form.

The form can be updated with more granular control by executing the `set_progress(current, total, description)` method of your form.

## How to use

Add the `FormTaskMixin` mixin to your `Form`:

```python
from django.forms import Form
from celery_formtask.forms import FormTaskMixin

class MyForm(FormTaskMixin, Form):
    ...
    def clean(self):
        self.set_progress(current=1, total=3, description="Validating something neat")
        ...

    def save(self):
        self.set_progress(current=2, total=3, description="Saving something neat")
        ...
        self.set_progress(current=3, total=3, description="Done")

...

form = MyForm(data)
async_result = form.enqueue()
```
