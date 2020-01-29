from django.db import models
from .common_info import CommonInfo
from django.urls import reverse
from .document_type import DocumentType
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def get_default_document_type():
    return DocumentType.objects.get(code="UN").pk


class DataDocument(CommonInfo):
    """
    A DataDocument object is a single source of Factotum data.
    """

    filename = models.CharField(
        max_length=255,
        verbose_name="file name",
        help_text="The name of the document's source file",
    )
    title = models.CharField(
        max_length=255, verbose_name="title", help_text="the title of the document"
    )
    subtitle = models.CharField(
        null=True,
        blank=True,
        max_length=250,
        default=None,
        verbose_name="subtitle",
        help_text="the subtitle of the document",
    )
    url = models.CharField(
        null=True,
        blank=True,
        max_length=375,
        validators=[URLValidator()],
        verbose_name="URL",
        help_text="an optional URL to the document's remote source",
    )
    raw_category = models.CharField(
        null=True,
        blank=True,
        max_length=1000,
        verbose_name="raw category",
        help_text="the category applied by the document's originating dataset",
    )
    data_group = models.ForeignKey(
        "DataGroup",
        on_delete=models.CASCADE,
        verbose_name="data group",
        help_text="the DataGroup object to which the document belongs. The type of the data group determines which document types the document might be among, and determines much of the available relationships and behavior associated with the document's extracted data",
    )
    products = models.ManyToManyField(
        "Product",
        through="ProductDocument",
        help_text="Products are associated with the data document in a many-to-many relationship",
    )
    matched = models.BooleanField(
        default=False,
        help_text="When a source file for the document has been uploaded to the file system, the document is considered matched to that source file. ",
    )

    document_type = models.ForeignKey(
        "DocumentType",
        on_delete=models.SET(get_default_document_type),
        default=get_default_document_type,
        verbose_name="document type",
        help_text="each type of data group may only contain certain types of data documents. The clean() method checks to make sure that the assigned document type is among the types allowed by the group type",
    )
    organization = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="organization",
        help_text="The organization that provided the source file",
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="note",
        help_text="Long-form notes about the document",
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(self.title)

    @property
    def detail_page_editable(self):
        # this could be moved to settings
        return self.data_group.group_type.code in ["CP", "HH", "CO"]

    @property
    def chemicals(self):
        return self.extractedtext.rawchem if self.is_extracted else []

    @property
    def is_extracted(self):
        """When the content of a data document has been extracted by manual data entry
        or by an extraction script, a new ExtractedText record is created
        with the DataDocument's id as its primary key.
        """
        return hasattr(self, "extractedtext")

    def get_absolute_url(self):
        return reverse("data_document", kwargs={"pk": self.pk})

    def get_abstract_filename(self):
        ext = self.filename.split(".")[-1]  # maybe not all are PDF??
        return f"document_{self.pk}.{ext}"

    def pdf_url(self):
        dg = self.data_group
        fn = self.get_abstract_filename()
        return f"/media/{dg.fs_id}/pdf/{fn}"

    def clean(self, skip_type_check=False):
        # the document_type must be one of the children types
        # of the datadocument's parent datagroup or null
        if (
            not skip_type_check
            and self.document_type
            and self.document_type not in DocumentType.objects.compatible(self)
        ):
            raise ValidationError(
                ("The document type must be allowed by the parent data group.")
            )
