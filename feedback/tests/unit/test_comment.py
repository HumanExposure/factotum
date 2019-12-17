from django.test import TestCase, RequestFactory
from django.utils.text import Truncator

from feedback.forms import CommentForm
from feedback.models import Comment as CommentModel


class TestCommentForm(TestCase):
    def test_valid_data(self):
        form = CommentForm({"email": "test@epa.gov", "body": "This is a valid test"})

        self.assertTrue(form.is_valid())

    def test_invalid_data(self):
        form_invalid_blank = CommentForm({})
        form_invalid_not_email = CommentForm({"email": "test"})
        form_invalid_not_epa = CommentForm({"email": "test@email.com"})

        # Blank Data
        self.assertEqual(
            form_invalid_blank.errors["email"], ["This field is required."]
        )
        self.assertEqual(form_invalid_blank.errors["body"], ["This field is required."])

        # Not an Email Address
        self.assertEqual(
            form_invalid_not_email.errors["email"], ["Enter a valid email address."]
        )

        # Not an EPA Email Address
        self.assertEqual(
            form_invalid_not_epa.errors["email"],
            [form_invalid_not_epa.epa_error_message],
        )

    def test_meta(self):
        self.assertEqual(CommentModel, CommentForm.Meta.model)
        self.assertEqual(["email", "body"], CommentForm.Meta.fields)


class TestCommentModel(TestCase):
    def setUp(self):
        self.email = "test@epa.gov"
        self.body = "test string"
        self.long_body = """This test string over 100 characters which will require truncation. 
                            This test will verify that the __str__ method properly truncates"""

        self.comment = CommentModel(email=self.email, body=self.body)
        self.long_comment = CommentModel(email=self.email, body=self.long_body)

    def test_str(self):
        # Verify the string form of a comment is "email: body"
        self.assertEqual("{0}: {1}".format(self.email, self.body), str(self.comment))
        # Verify long bodies get truncated at 100 characters.
        self.assertEqual(
            "{0}: {1}".format(self.email, Truncator(self.long_body).chars(100)),
            str(self.long_comment),
        )
