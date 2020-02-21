import os

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from dashboard.forms.bulk_document_forms import DocBulkFormSet
from dashboard.utils import gather_errors, zip_stream


class BulkDocuments(View):
    """
    The basic GET version of the view
    """

    template_name = "get_data/bulk_documents.html"

    def get(self, request):
        formset = DocBulkFormSet()
        return render(request, self.template_name, context={"formset": formset})

    def post(self, request, *args, **kwargs):
        """
        The user uploads a csv file of document ids, the server returns a zip file
        containing all those documents' pdfs.
        """
        formset = DocBulkFormSet(request.POST, request.FILES)
        formset.is_valid()
        valid_docs = lambda: (
            f.cleaned_data["id"] for f in formset.forms if f.cleaned_data
        )
        errors = tuple(gather_errors(formset, values=True))
        if any(valid_docs()):
            # This will fail with a 500 if the file doesn't exist. We're not catching
            # that because if we got this far, we know the file SHOULD exist: we are
            # only working with Documents that have match=True. If this fails, we
            # have some kind of data integrity issue (or you're a dev without the files)
            files = {
                f"datadocument_{doc.pk}{os.path.splitext(doc.file.name)[1]}": doc.file.path
                for doc in valid_docs()
            }
            data = {"errors.txt": str.encode("\n".join(errors))} if errors else {}
            response = zip_stream(files, data, filename="datadocuments.zip")
            if errors:
                response.status_code = 206
            else:
                response.status_code = 200
            return response
        else:
            for e in errors:
                messages.error(request, e)
            return HttpResponseRedirect(reverse("bulk_documents"))
