from taggit.managers import TaggableManager

from django.db import models

from .common_info import CommonInfo
from .extracted_habits_and_practices_to_puc import ExtractedHabitsAndPracticesToPUC
from .extracted_habits_and_practices import ExtractedHabitsAndPractices


class PUC(CommonInfo):
    gen_cat = models.CharField(max_length=50, blank=False)
    prod_fam = models.CharField(max_length=50, null=True, blank=True)
    prod_type = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=False, blank=False)
    last_edited_by = models.ForeignKey('auth.User', default=1, on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', through='ProductToPUC')
    extracted_habits_and_practices = models.ManyToManyField('dashboard.ExtractedHabitsAndPractices',
                                                            through='dashboard.ExtractedHabitsAndPracticesToPUC')
    tags = TaggableManager(through='dashboard.PUCToTag',
                           to='dashboard.PUCTag',
                           help_text='A set of PUC Tags applicable to this PUC')

    class Meta:
        ordering = ['gen_cat', 'prod_fam', 'prod_type']
        verbose_name_plural = 'PUCs'

    def __str__(self):
        cats = [self.gen_cat, self.prod_fam, self.prod_type]
        return ' - '.join(cat for cat in cats if cat is not None)

    def natural_key(self):
        return self.gen_cat

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    def get_the_kids(self):
        if not self.prod_fam and not self.prod_type:
            return PUC.objects.filter(gen_cat=self.gen_cat)
        if self.prod_fam and not self.prod_type:
            return PUC.objects.filter(gen_cat=self.gen_cat,
                                        prod_fam=self.prod_fam)
        if self.prod_fam and self.prod_type:
            return PUC.objects.filter(pk=self.pk)
