from dal import autocomplete
from django import forms

from dashboard.models import (
    ExtractedListPresence,
    ExtractedListPresenceTag,
    ExtractedHabitsAndPractices,
    ExtractedHabitsAndPracticesTag,
    ExtractedHabitsAndPracticesToTag,
)


class ExtractedListPresenceTagForm(autocomplete.FutureModelForm):
    class Meta:
        model = ExtractedListPresence
        fields = ["tags"]

        widgets = {
            "tags": autocomplete.TaggitSelect2("list_presence_tags_autocomplete")
        }

    def __init__(self, *args, **kwargs):
        super(ExtractedListPresenceTagForm, self).__init__(*args, **kwargs)
        self.fields["tags"].widget.attrs.update(
            {"class": "mr-2 ml-2", "style": "width:60%", "data-minimum-input-length": 3}
        )
        self.fields["tags"].label = ""
        self.fields["tags"].help_text = ""

    def clean(self):
        valid_tag_list = ExtractedListPresenceTag.objects.all().values_list(
            "name", flat=True
        )
        self.invalid_tags = []
        existing_tags = list(self.instance.tags.values_list("name", flat=True))
        self.cleaned_data["tags"] += existing_tags
        for tag in self.cleaned_data["tags"]:
            if tag in valid_tag_list:
                pass
            else:
                self.invalid_tags.append(tag)
                self.cleaned_data["tags"].remove(tag)
                self.add_error("tags", "%s is not a valid keyword" % tag)


class ExtractedHabitsAndPracticesTagForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=ExtractedHabitsAndPracticesTag.objects.all(),
        label="",
        widget=autocomplete.ModelSelect2Multiple(
            url="habits_and_practices_tags_autocomplete",
            attrs={"data-minimum-input-length": 3, "style": "width: 100%"},
        ),
    )

    class Meta:
        model = ExtractedHabitsAndPractices
        fields = ["tags"]

    def save(self, commit=True):
        """Overridden to add existing tags prior to save.
        (Keyword saves are non-destructive)
        """
        existing_tags = self.instance.tags.all()
        self.cleaned_data["tags"] = existing_tags | self.cleaned_data["tags"]
        super().save(commit)