from django import forms
from dashboard.models import DataDocument
from bulkformsets import csvformset_factory


class DocCSVForm(forms.Form):
    id = forms.ModelChoiceField(DataDocument.objects.exclude(file=""))


DocBulkFormSet = csvformset_factory(
    DocCSVForm, extra=0, validate_max=True, min_num=1, validate_min=True
)
