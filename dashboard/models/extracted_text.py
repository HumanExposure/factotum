from django.db import models
from .common_info import CommonInfo
from datetime import datetime
from django.core.exceptions import ValidationError
from django import forms
from .data_document import DataDocument
from .script import Script
from itertools import chain

class ExtractedText(CommonInfo):
    data_document = models.OneToOneField(DataDocument,on_delete=models.CASCADE,
                                                            primary_key=True)
    prod_name = models.CharField(max_length=500, null=True, blank=True)
    doc_date = models.CharField(max_length=25, null=True, blank=True)
    rev_num = models.CharField(max_length=50, null=True, blank=True)
    extraction_script = models.ForeignKey(
        Script, on_delete=models.CASCADE, limit_choices_to={'script_type': 'EX'}, )
    qa_checked = models.BooleanField(default=False, verbose_name="QA approved")
    qa_edited = models.BooleanField(default=False, verbose_name="QA edited")
    qa_approved_date = models.DateTimeField(null=True, blank=True, verbose_name="QA approval date")
    qa_approved_by = models.ForeignKey(
        'auth.User', null=True, blank=True, on_delete=models.SET_NULL, verbose_name = "QA approved by")
    qa_group = models.ForeignKey('QAGroup', null=True, blank=True, verbose_name="QA group",
                                 on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.prod_name)

    def next_extracted_text_in_qa_group(self):
        nextid = 0
        extextnext = get_next_or_prev(ExtractedText.objects.filter(
            qa_group=self.qa_group, qa_checked=False), self, 'next')
        if extextnext:
            # Replace our item with the next one
            nextid = extextnext.pk
        if extextnext == self:
            nextid = 0
        return nextid

    def fetch_extracted_records(self):
        '''Collect the related objects in all the Extracted... models
        '''
        # Start with the known children of the base Model: ExtractedText
        full_chain = chain(self.practices.all(), 
                    self.chemicals.all(), 
                    self.uses.all()
                    )
        # Try to get all the child objects of derived (inherited) models

        # ExtractedCPCat has related ExtractedListPresence objects connected
        # by the .presence relation
        if hasattr(self, 'extractedcpcat'):
            presence_chain = self.extractedcpcat.presence.all()
            full_chain = chain(full_chain, presence_chain)

        return full_chain
        

            

                



def get_next_or_prev(models, item, direction):
    '''
    Returns the next or previous item of
    a query-set for 'item'.

    'models' is a query-set containing all
    items of which 'item' is a part of.

    direction is 'next' or 'prev'

    '''
    getit = False
    if direction == 'prev':
        models = models.reverse()
    for m in models:
        if getit:
            return m
        if item == m:
            getit = True
    if getit:
        # This would happen when the last
        # item made getit True
        return models[0]
    return False
