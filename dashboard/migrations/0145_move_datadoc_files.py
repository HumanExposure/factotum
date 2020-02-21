import logging
import os
import shutil
import uuid

import dashboard.models.data_document
from django.conf import settings
from django.db import migrations, models


def make_unique_files_in_db(apps, schema_editor):
    """Updates DataDocument.file to UUID files"""
    DataDocument = apps.get_model("dashboard", "DataDocument")
    updated_docs = []
    chunk_size = 2000
    cnt = 0
    for d in DataDocument.objects.extra(select={"matched": "matched"}).iterator(
        chunk_size=chunk_size
    ):
        cnt += 1
        if d.matched:
            _, ext = os.path.splitext(d.filename)
            d.file = f"{uuid.uuid4()}{ext}"
            updated_docs.append(d)
        if updated_docs and cnt % chunk_size == 0:
            DataDocument.objects.bulk_update(updated_docs, ["file"])
            updated_docs = []
    if updated_docs:
        DataDocument.objects.bulk_update(updated_docs, ["file"])


def move_files(apps, schema_editor):
    """Move files from DataGroup folder to the base of MEDIA_ROOT"""
    DataDocument = apps.get_model("dashboard", "DataDocument")
    media_base = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT)
    archive_base = os.path.join(media_base, "0145_remaining_files")
    # We don't need to do this on an empty database
    if DataDocument.objects.exists():
        # First, move old files into the folder 0145_remaining_files
        if not os.path.exists(media_base):
            os.mkdir(archive_base)
        old_files = os.listdir(media_base)
        if not os.path.exists(media_base):
            os.mkdir(archive_base)
        for f in old_files:
            original_path = os.path.join(media_base, f)
            archive_path = os.path.join(archive_base, f)
            shutil.move(original_path, archive_path)
        # Now, move files from 0145_remaining_files into a flat dump in MEDIA_ROOT
        logger = logging.getLogger(__name__)
        DataDocument = apps.get_model("dashboard", "DataDocument")
        for d in DataDocument.objects.extra(
            select={
                "csv": "select csv from dashboard_datagroup where dashboard_datagroup.id = dashboard_datadocument.data_group_id",
                "fs_id_str": "select fs_id from dashboard_datagroup where dashboard_datagroup.id = dashboard_datadocument.data_group_id",
                "matched": "matched",
            }
        ).iterator():
            if d.matched:
                fs_id = str(uuid.UUID(d.fs_id_str))
                csv_root = os.path.dirname(d.csv)
                _, ext = os.path.splitext(d.filename)
                archive_filename = f"datadocument_{d.pk}{ext}"
                archive_path = os.path.join(
                    archive_base, fs_id, "pdf", archive_filename
                )
                archive_path_legacy = os.path.join(
                    archive_base, csv_root, "pdf", archive_filename
                )
                if os.path.exists(archive_path):
                    shutil.move(archive_path, d.file.path)
                elif os.path.exists(archive_path_legacy):
                    shutil.move(archive_path_legacy, d.file.path)
                else:
                    logger.warn(f"DataDocument not found (ID {d.pk})")


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0144_create_extratedhabitsandpracticesdatatype")]

    operations = [
        migrations.AddField(
            model_name="datadocument",
            name="file",
            field=models.FileField(
                default="",
                help_text="The document's source file",
                max_length=255,
                null=False,
                blank=True,
                upload_to=dashboard.models.data_document.uuid_file,
                verbose_name="file",
            ),
        ),
        migrations.RunPython(make_unique_files_in_db, migrations.RunPython.noop),
        migrations.RunPython(move_files, migrations.RunPython.noop),
        migrations.RemoveField(model_name="datadocument", name="matched"),
        migrations.RemoveField(model_name="datagroup", name="csv"),
        migrations.RemoveField(model_name="datagroup", name="fs_id"),
        migrations.RemoveField(model_name="datagroup", name="zip_file"),
    ]
