import tempfile


class DashboardFormFieldTestMixin:
    """This class mixes in some useful methods for testing dashboard form fields.
    It expects a form to be set in self.
    """

    def field_exists(self, field):
        """Checks if a field exists in a Django ModelForm.
        Arguments:
            ``field``
                a string representing the field name
        """
        self.assertTrue(
            field in self.form._meta.fields,
            f'"{self.form.__name__}"" does not include field "{field}"',
        )

    def fields_exclusive(self, fields):
        """Checks if a Django ModelForm contains only certain fields
        Arguments:
            ``fields``
                an iterable of strings representing the field names
        """
        s = set(self.form._meta.fields)
        for f in fields:
            self.field_exists(f)
            s.discard(f)
        self.assertTrue(
            not len(s), f'"{self.form.__name__}"" includes extra fields "{s}"'
        )

    def post_field(self, post_uri, field, data, pk=None):
        """Checks if a Django ModelForm can correctly POST all its fields.
        Arguments
            ``post_uri``
                a string representing the relative root POST uri
            ``field``
                a string representing the field name
            ``data``
                data to post to field
        Keyword arguments:
            ``pk = None``
                A specific Model pk to test against. Otherwise,
                an arbitrary object will be chosen.
        """
        # ensure trailing slash
        if post_uri[-1] != "/":
            post_uri += "/"
        # get object
        qs = self.form._meta.model.objects
        if pk:
            obj = qs.get(pk=pk)
        else:
            obj = qs.first()
        # attempt to correct foreign key naming
        if field not in obj.__dict__ and field + "_id" in obj.__dict__:
            dict_field = field + "_id"
        else:
            dict_field = field
        # generate data to post with
        post_data = {}
        for key in self.form._meta.fields:
            # non foreign key
            if key in obj.__dict__:
                value = obj.__dict__[key]
            # foreign key
            elif key + "_id" in obj.__dict__:
                value = obj.__dict__[key + "_id"]
            # don't include nulls
            if (value is not None) or (value is None and key == field):
                post_data[key] = value
        self.assertTrue(
            post_data[field] != data,
            f'Bad attempt to update "{type(obj).__name__}" with identical data on field "{field}"',
        )
        post_data[field] = data
        response = self.client.post(post_uri + str(obj.pk) + "/", post_data)
        obj.refresh_from_db()
        self.assertTrue(
            obj.__dict__[dict_field] == data,
            f'POST error with object "{type(obj).__name__}" '
            f'on field "{field}" '
            f'at "{post_uri}"',
        )


class TempFileMixin:
    """This class makes Django's media storage be a temporary directory.
    It helps isolate tests from one another and cluttering the /media/ folder.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        settings = {"MEDIA_ROOT": cls._tmpdir.name}
        if cls._overridden_settings:
            cls._overridden_settings.update(settings)
        else:
            cls._overridden_settings = settings
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls._tmpdir = None
        super().tearDownClass()
