import os
import shutil
import uuid
from factotum import settings

from django.db import models
from .common_info import CommonInfo
from django.urls import reverse
from django.dispatch import receiver
from .group_type import GroupType


# could be used for dynamically creating filename on instantiation
# in the 'upload_to' param on th FileField
def update_filename(instance, filename):
    name_fill_space = instance.name.replace(' ', '_')
    name = '{0}/{0}_{1}'.format(name_fill_space, filename) # potential space errors in name
    return name


def csv_upload_path(instance, filename):
    name = '{0}/{1}'.format(instance.fs_id, filename) # potential space errors in name
    return name


class DataGroup(CommonInfo):

    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    downloaded_by = models.ForeignKey('auth.User', on_delete=models.SET_DEFAULT, default = 1)
    downloaded_at = models.DateTimeField()
    download_script = models.ForeignKey('Script', on_delete=models.SET_NULL, default=None, null=True, blank=True)
    data_source = models.ForeignKey('DataSource', on_delete=models.CASCADE)
    fs_id = models.UUIDField(default=uuid.uuid4, editable=False)
    csv = models.FileField(upload_to=csv_upload_path, null=True)
    zip_file = models.CharField(max_length=100)
    group_type = models.ForeignKey(GroupType, on_delete=models.SET_DEFAULT, default=1, null=True, blank=True)
    url = models.CharField(max_length=150, blank=True)

    def save(self, *args, **kwargs):
        super(DataGroup, self).save(*args, **kwargs)

    def matched_docs(self):
        return self.datadocument_set.filter(matched=True).count()

    def all_matched(self):
        return all(self.datadocument_set.values_list('matched', flat=True))

    def all_extracted(self):
        return all(self.datadocument_set.values_list('extracted', flat=True))

    def registered_docs(self):
        return self.datadocument_set.count()

    def extracted_docs(self):
        return self.datadocument_set.filter(extracted=True).count()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('data_group_edit', kwargs={'pk': self.pk})

    def get_dg_folder(self):
        uuid_dir = f'{settings.MEDIA_ROOT}{str(self.fs_id)}'
        name_dir = f'{settings.MEDIA_ROOT}{self.get_name_as_slug()}'
        csv_dir  = f'{settings.MEDIA_ROOT}{self.csv.path.split(sep="/")[0]}'
        if os.path.isdir(uuid_dir):
            return uuid_dir # UUID-based folder
        elif os.path.isdir(name_dir):
            return name_dir # name-based folder
        elif os.path.isdir(csv_dir):
            return csv_dir # name-based folder
        else:
            return 'no_folder_found'

    def get_name_as_slug(self):
        return self.name.replace(' ', '_')
    
    def get_zip_url(self):
        # the path if the data group's folder was built from a UUID:
        uuid_path = f'{self.get_dg_folder()}/{str(self.fs_id)}.zip'
        # the path if the data group's folder was built from the old name-based method
        zip_file_path = f'{self.get_dg_folder()}/{str(self.get_name_as_slug())}.zip'
        if os.path.isfile(uuid_path):   # it is a newly-added data group
            zip_url = uuid_path
        elif os.path.isfile(zip_file_path): # it is a pre-UUID data group
            zip_url = zip_file_path
        else:
            zip_url = 'no_path_found'
        return zip_url


@receiver(models.signals.post_delete, sender=DataGroup)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes datagroup directory from filesystem
    when datagroup instance is deleted.
    """
    dg_folder = instance.get_dg_folder()
    if os.path.isdir(dg_folder):
        #print('deleting folder %s for data group %s' % (dg_folder, instance.pk))
        shutil.rmtree(dg_folder)
