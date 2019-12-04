from model_utils.managers import InheritanceManager

from django.db import models
from django.urls import reverse

from .common_info import CommonInfo

# this could potentially be used for 1:1 matching when uploading
# coming in django v2.2!!
# class Meta:
# 	constraints = [
# 		models.UniqueConstraint(fields=['prod_name','data_document'],
# 								name='unique_assignment'),
# 	]


class ExtractedText(CommonInfo):
    data_document = models.OneToOneField(
        "DataDocument", on_delete=models.CASCADE, primary_key=True
    )
    prod_name = models.CharField(
        "Product name",
        max_length=500,
        null=True,
        blank=True,
        help_text="The name of the product according to the extracted document",
    )
    doc_date = models.CharField("Document date", max_length=25, null=True, blank=True)
    rev_num = models.CharField("Revision number", max_length=50, null=True, blank=True)
    extraction_script = models.ForeignKey(
        "Script", on_delete=models.CASCADE, limit_choices_to={"script_type": "EX"}
    )
    qa_checked = models.BooleanField(default=False, verbose_name="QA approved")
    qa_edited = models.BooleanField(default=False, verbose_name="QA edited")
    qa_approved_date = models.DateTimeField(
        null=True, blank=True, verbose_name="QA approval date"
    )
    qa_approved_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        verbose_name="QA approved by",
        null=True,
        blank=True,
    )
    qa_group = models.ForeignKey(
        "QAGroup",
        verbose_name="QA group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    objects = InheritanceManager()

    def __str__(self):
        return str(self.data_document)

    def next_extracted_text_in_qa_group(self):
        nextid = 0
        # If the document is part of a Script-based QA Group, the
        # next document is drawn from that group. If it is a CPCat
        # or HHE record, there is no next document
        extextnext = get_next_or_prev(
            ExtractedText.objects.filter(qa_group=self.qa_group, qa_checked=False),
            self,
            "next",
        )
        if extextnext:
            # Replace our item with the next one
            nextid = extextnext.pk
        if extextnext == self:
            nextid = 0
        return nextid

    def get_qa_index_path(self):
        """
        The type of data group to which the extracted text object belongs
        determines which QA index it will use.
        """
        group_type_code = self.data_document.data_group.group_type.code

        if group_type_code in ["CP", "HH"]:
            # TODO: change HH to its own path
            return reverse("qa_chemicalpresence_index")
        else:
            return reverse("qa_extractionscript_index")

    def one_to_one_check(self, odict):
        """
        Used in the upload of extracted text in the data_group_detail view, this
        returns a boolean to assure that there is a 1:1 relationship w/
        the Extracted{parent}, i.e. (Text/CPCat), and the DataDocument
        """
        if hasattr(self, "cat_code"):
            return self.cat_code != odict["cat_code"]
        else:
            return self.prod_name != odict["prod_name"]

    def is_approvable(self):
        """
        Returns true or false to indicate whether the ExtractedText object
        can be approved. If the object has been edited, then there must be
        some related QA Notes.

        Note that if the ExtractedText object is missing a related QANotes
        record, self.qanotes will not return None. Instead it returns an 
        ObjectDoesNotExist error.
        https://stackoverflow.com/questions/3463240/check-if-onetoonefield-is-none-in-django

        The hasattr() method is the correct way to test for the presence of 
        a related record.

        It is not enough to test for the related record, though, because an empty
        qa_notes field is functionally equivalent to a missing QANotes record.

        """

        if not self.qa_edited:
            return True
        elif self.qa_edited and not hasattr(self, "qanotes"):
            return False
        elif (
            self.qa_edited
            and hasattr(self, "qanotes")
            and not bool(self.qanotes.qa_notes)
        ):
            return False
        else:
            return True


def get_next_or_prev(models, item, direction):
    """
    Returns the next or previous item of
    a query-set for 'item'.

    'models' is a query-set containing all
    items of which 'item' is a part of.

    direction is 'next' or 'prev'

    """
    getit = False
    if direction == "prev":
        models = models.reverse()
    for m in models:
        if getit:
            return m
        if item == m:
            getit = True
    if getit:
        # This would happen when the last
        # item made getit True
        return models[0]
    return False
