from django.shortcuts import render, redirect
from django import views

from feedback.models.comment import Comment as CommentModel
from feedback.forms.comment_form import CommentForm


class Comment(views.View):
    model = CommentModel
    form_class = CommentForm
    template_name = "feedback/comment_create.html"

    def get(self, request):
        return render(request, self.template_name, {"form": self.form_class})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()
            return redirect("feedback:comment")

        return render(request, self.template_name, {"form": form}, status=422)
