from taggit_labels.widgets import LabelWidget

from django.utils import six
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe


class FilteredLabelWidget(LabelWidget):
    # overriding django-taggit-label function to display subset of tags
    def tag_list(self, tags):
        # must set form_instance in form __init__()
        puc = self.form_instance.instance.uber_puc
        qs = self.model.objects.filter(content_object=puc, assumed=False)
        filtered = [unassumed.tag for unassumed in qs]
        return [
            (
                tag.name,
                "selected taggit-tag" if tag.name in tags else "taggit-tag",
                tag.definition,
            )
            for tag in filtered
        ]

    # swiped and modified from taggit-labels on github
    def render(self, name, value, attrs={}, **kwargs):
        # Case in which a new form is dispalyed
        if value is None:
            current_tags = []
            formatted_value = ""
            selected_tags = self.tag_list([])

        # Case in which a form is displayed with submitted but not saved
        # details, e.g. invalid form submission
        elif isinstance(value, six.string_types):
            current_tags = [tag.strip(' "') for tag in value.split(",") if tag]
            formatted_value = value
            selected_tags = self.tag_list(current_tags)

        # Case in which value is loaded from saved tags
        else:
            current_tags = [o.tag for o in value.select_related("tag")]
            formatted_value = self.format_value(value)
            selected_tags = self.tag_list([t.name for t in current_tags])

        input_field = super(LabelWidget, self).render(
            name, formatted_value, attrs, **kwargs
        )
        if attrs.get("class") is None:
            attrs.update({"class": "taggit-labels taggit-list"})
        list_attrs = flatatt(attrs)

        tag_li = "".join(
            [
                u"<li data-tag-name='{0}' title='{2}' class='{1}'>{0}</li>".format(
                    tag[0], tag[1], tag[2] if tag[2] else "No definition"
                )
                for tag in selected_tags
            ]
        )
        tag_ul = u"<ul{0}>{1}</ul>".format(list_attrs, tag_li)
        return mark_safe(u"{0}{1}".format(tag_ul, input_field))
