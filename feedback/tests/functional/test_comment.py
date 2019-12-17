from django.shortcuts import render
from django.test import TestCase, RequestFactory
from django.urls import reverse
from lxml import html

from feedback.views import Comment as CommentView
from feedback.forms import CommentForm


class TestComment(TestCase):
    create_path_name = "feedback:comment"

    # Test that GET requests to feedback:comment return a page built using core and feedback templates.
    def test_get_create_view(self):
        response = self.client.get(reverse(self.create_path_name))

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            CommentView.as_view().__name__, response.resolver_match.func.__name__
        )

        self.assertTemplateUsed(response, template_name="core/base.html")
        self.assertTemplateUsed(response, template_name="core/bs4_form.html")
        self.assertTemplateUsed(response, template_name="feedback/comment_create.html")

    # Test that valid POST data returns a "302 - Redirect" and sends user to "feedback:comment" page
    def test_post_valid_data_create_comment(self):
        response = self.client.post(
            reverse(self.create_path_name),
            {"email": "test@epa.gov", "body": "Valid body"},
        )

        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse(self.create_path_name))
        self.assertEqual(
            CommentView.as_view().__name__, response.resolver_match.func.__name__
        )

    # Test that invalid POST data returns a "422 - Unprocessable Entity" status code
    # and that error messages are returned.
    def test_post_invalid_data_create_comment(self):
        blank_response = self.client.post(reverse(self.create_path_name), {})
        invalid_email_response = self.client.post(
            reverse(self.create_path_name), {"email": "test@email.com"}
        )

        self.assertEqual(422, blank_response.status_code)
        self.assertFormError(
            blank_response, "form", "email", u"This field is required."
        )
        self.assertFormError(blank_response, "form", "body", u"This field is required.")

        self.assertEqual(422, invalid_email_response.status_code)
        self.assertFormError(
            invalid_email_response, "form", "email", CommentForm.epa_error_message
        )


class TestCommentCreateTemplate(TestCase):
    create_path_name = "feedback:comment"

    def setUp(self):
        self.factory = RequestFactory()
        self.template_name = "feedback/comment_create.html"
        self.form = CommentForm({})

    def test_comment_create_page(self):
        response = render(
            self.factory.get(reverse(self.create_path_name)),
            self.template_name,
            {"form": self.form},
        )
        page = html.fromstring(response.content)

        # Assert form has required inputs.
        self.assertTrue(page.xpath('//input[@id="id_email"]'))
        self.assertTrue(page.xpath('//textarea[@id="id_body"]'))
