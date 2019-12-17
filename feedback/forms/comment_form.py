from django import forms

from feedback.models import Comment


class CommentForm(forms.ModelForm):
    required_css_class = "required"
    epa_error_message = "Email must be @epa.gov"

    class Meta:
        model = Comment
        fields = ["email", "body"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "email.address@epa.gov"}),
            "body": forms.Textarea,
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if email and not email.endswith("@epa.gov"):
            self.add_error("email", self.epa_error_message)
