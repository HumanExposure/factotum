from django import forms
from django.db import transaction
from django.utils import timezone

from dashboard.utils import clean_dict
from dashboard.forms.data_group import DGFormSet
from dashboard.models.dsstox_lookup import validate_prefix, validate_blank_char
from dashboard.models import DataGroup, RawChem, DSSToxLookup
from bulkformsets import CSVReader


class DGChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        recs = obj.uncurated_count()
        return "%i: %s (%i records)" % (obj.pk, obj.name, recs)


class DataGroupSelector(forms.ModelForm):
    data_group = DGChoiceField(
        queryset=DataGroup.objects.filter(
            pk__in=[dg.pk for dg in DataGroup.objects.all() if dg.uncurated]
        ),
        label="Download Uncurated Chemicals by Data Group",
        required=False,
    )

    class Meta:
        model = DataGroup
        fields = ("id",)


class ChemicalCurationForm(forms.Form):

    external_id = forms.ModelChoiceField(queryset=RawChem.objects.all())
    rid = RawChem._meta.get_field("rid").formfield()
    sid = DSSToxLookup._meta.get_field("sid").formfield()
    true_chemical_name = DSSToxLookup._meta.get_field("true_chemname").formfield()
    true_cas = DSSToxLookup._meta.get_field("true_cas").formfield()

    def __init__(self, *args, **kwargs):
        super(ChemicalCurationForm, self).__init__(*args, **kwargs)
        sid_field = self.fields["sid"]
        sid_field.validators.append(validate_prefix)
        sid_field.validators.append(validate_blank_char)


class ChemicalCurationFormSet(DGFormSet):
    prefix = "curate"
    serializer = CSVReader

    def __init__(self, *args, **kwargs):
        fields = ["external_id", "rid", "sid", "true_chemical_name", "true_cas"]
        self.form = ChemicalCurationForm
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        header = list(self.bulk.fieldnames)
        header_cols = ["external_id", "rid", "sid", "true_chemical_name", "true_cas"]
        if header != header_cols:
            raise forms.ValidationError(f"CSV column titles should be {header_cols}")

    def save(self):
        new_dsstox = []
        made_dsstox = []
        update_chems = []
        for form in self.forms:
            form.cleaned_data["true_chemname"] = form.cleaned_data["true_chemical_name"]
            dss_dict = clean_dict(form.cleaned_data, DSSToxLookup)
            if DSSToxLookup.objects.filter(**dss_dict).exists():
                dss = DSSToxLookup.objects.get(**dss_dict)
            else:
                if DSSToxLookup.objects.filter(sid=dss_dict["sid"]).exists():
                    dss = DSSToxLookup.objects.get(sid=dss_dict["sid"])
                    dss.true_chemname = dss_dict["true_chemname"]
                    dss.true_cas = dss_dict["true_cas"]
                    dss.updated_at = timezone.now()
                    made_dsstox.append(dss)
                else:
                    dss = DSSToxLookup(**dss_dict)
                    new_dsstox.append(dss)
            chem = form.cleaned_data["external_id"]
            chem.dsstox = dss
            chem.rid = form.cleaned_data["rid"]
            update_chems.append(chem)
        with transaction.atomic():
            DSSToxLookup.objects.bulk_create(new_dsstox)
            DSSToxLookup.objects.bulk_update(
                made_dsstox, ["true_chemname", "true_cas", "updated_at"]
            )
            RawChem.objects.bulk_update(update_chems, ["dsstox", "rid"])
        return len(self.forms)
