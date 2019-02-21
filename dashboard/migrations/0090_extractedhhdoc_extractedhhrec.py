# Generated by Django 2.1.2 on 2019-02-15 01:32

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields

def add_hh_grouptype(apps, schema_editor):
    '''
    if it not already there, add a new grouptype
    for HHE Reports
    '''
    GroupType = apps.get_model('dashboard', 'GroupType')
    DocumentType = apps.get_model('dashboard', 'DocumentType')
    gt, gt_created = GroupType.objects.get_or_create(title='HHE Report',code='HH')
    if not DocumentType.objects.filter(code='HH').exists():
        DocumentType.objects.create(title='HHE Report',code='HH', group_type=gt)

def remove_hh_grouptype(apps, schema_editor):
    '''
    Remove the HHE Reports grouptype and document types
    '''
    GroupType = apps.get_model('dashboard', 'GroupType')
    DocumentType = apps.get_model('dashboard', 'DocumentType')

    if DocumentType.objects.filter(code='HH').exists:
        DocumentType.objects.filter(code='HH').delete()

    if GroupType.objects.filter(code='HH').exists:
        GroupType.objects.filter(code='HH').delete()

    

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0089_puc_fields'),
    ]

    operations = [
        migrations.RunPython(add_hh_grouptype,reverse_code=remove_hh_grouptype),

        migrations.CreateModel(
            name='ExtractedHHDoc',
            fields=[
                ('extractedtext_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='dashboard.ExtractedText')),
                ('hhe_report_number', models.CharField(max_length=30, verbose_name='HHE Report Number')),
                ('study_location', models.CharField(blank=True, max_length=50, null=True, verbose_name='Study Location')),
                ('naics_code', models.CharField(blank=True, max_length=10, null=True, verbose_name='NAICS Code')),
                ('sampling_date', models.CharField(blank=True, max_length=75, null=True, verbose_name='Date of Sampling')),
                ('population_gender', models.CharField(blank=True, max_length=75, null=True, verbose_name='Gender of Population')),
                ('population_age', models.CharField(blank=True, max_length=75, null=True, verbose_name='Age of Population')),
                ('population_other', models.CharField(blank=True, max_length=255, null=True, verbose_name='Other Description of Population')),
                ('occupation', models.CharField(blank=True, max_length=75, null=True, verbose_name='Occupation')),
                ('facility', models.CharField(blank=True, max_length=75, null=True, verbose_name='Facility')),
            ],
            options={
                'abstract': False,
            },
            bases=('dashboard.extractedtext',),
        ),
        migrations.CreateModel(
            name='ExtractedHHRec',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('media', models.CharField(blank=True, max_length=30, null=True, verbose_name='Media')),
                ('sampling_method', models.TextField(blank=True, null=True, verbose_name='Sampling Method')),
                ('analytical_method', models.TextField(blank=True, null=True, verbose_name='Analytical Method')),
                ('num_measure', models.CharField(blank=True, max_length=50, null=True, verbose_name='Numeric Measure')),
                ('num_nondetect', models.CharField(blank=True, max_length=50, null=True, verbose_name='Numeric Nondetect')),
                ('rawchem_ptr', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='hhrecord', serialize=False, to='dashboard.RawChem')),
                ('extracted_hhdoc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hhrecord', to='dashboard.ExtractedHHDoc')),
            ],
            options={
                'abstract': False,
            },
            bases=('dashboard.rawchem', models.Model),
        ),

    ]
