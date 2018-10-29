from urllib import parse

from django.urls import resolve
from django.utils import timezone, safestring
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from dashboard.models import *
from dashboard.forms import (ProductPUCForm, ProductLinkForm,
                             ProductForm)

from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget
from django.core.paginator import Paginator

class FilteredLabelWidget(LabelWidget):
    # overriding django-taggit-label function to display subset of tags
    def tag_list(self, tags):
        # must set form_instance in form __init__()
        puc = self.form_instance.instance.get_uber_puc() or None
        return [(tag.name, 'selected taggit-tag' if tag.name in tags else 'taggit-tag')
                for tag in self.model.objects.filter(puc = puc)]

class ProductTagForm(ModelForm):
    tags = TagField(required=False, widget=FilteredLabelWidget(model=PUCTag))
    class Meta:
        model = Product
        fields = ['tags']
    def __init__(self, *args, **kwargs):
        super(ProductTagForm, self).__init__(*args, **kwargs)
        self.fields['tags'].widget.form_instance = self


@login_required()
def product_curation_index(request, template_name='product_curation/product_curation_index.html'):
    # List of all data sources which have had at least 1 data
    # document matched to a registered record
    data_sources = DataSource.objects.annotate(uploaded=Count('datagroup__datadocument'))\
        .filter(uploaded__gt=0)
    # A separate queryset of data sources and their related products without PUCs assigned
    # Changed in issue 232. Instead of filtering products based on their prod_cat being null,
    #   we now exclude all products that have a product_id contained in the ProductToPUC object set
    qs_no_puc = Product.objects.values('data_source').exclude(id__in=(ProductToPUC.objects.values_list('product_id', flat=True))).\
        filter(data_source__isnull=False).annotate(no_category=Count('id')).order_by('data_source')
    # Convert the queryset to a list
    list_no_puc = [ds_no_puc for ds_no_puc in qs_no_puc]

    for ds in data_sources:
        try:
            ds.no_category = next((item for item in list_no_puc if item["data_source"] == ds.id), False)['no_category']
        except:
            ds.no_category = 0
        dgs = ds.datagroup_set.all()
        for dg in dgs:
            dg.unlinked = dg.datadocument_set.count() - dg.datadocument_set.filter(productdocument__document__isnull=False).count()
        ds.data_groups = dgs

    return render(request, template_name, {'data_sources': data_sources})

@login_required()
def category_assignment(request, pk, template_name=('product_curation/'
                                                'category_assignment.html')):
    """Deliver a datasource and its associated products"""
    ds = DataSource.objects.get(pk=pk)
    products = ds.source.exclude(id__in=(ProductToPUC.objects.values_list('product_id', flat=True))).order_by('-created_at')
    return render(request, template_name, {'datasource': ds, 'products': products})

@login_required()
def link_product_list(request,  pk, template_name='product_curation/link_product_list.html'):
    dg = DataGroup.objects.get(pk=pk)
    documents = dg.datadocument_set.filter(productdocument__document__isnull=True)
    npage = 20 # TODO: make this dynamic someday in its own ticket
    paginator = Paginator(documents, npage) # Show npage data documents per page
    page = request.GET.get('page')
    page = 1 if page is None else page
    docs_page = paginator.page(page)
    return render(request, template_name, {'documents':docs_page, 'datagroup':dg})

@login_required()
def link_product_form(request, pk, template_name=('product_curation/'
                                                    'link_product_form.html')):
    doc = DataDocument.objects.get(pk=pk)
    ds_id = doc.data_group.data_source_id
    upc_stub = ('stub_' + str(Product.objects.all().count() + 1))
    form = ProductLinkForm(initial={'upc': upc_stub, 'document_type': doc.document_type})
    # limit document type options to those matching parent datagroup group_type
    form.fields['document_type'].queryset =\
        form.fields['document_type'].queryset.filter(group_type_id = doc.data_group.group_type_id)
    if request.method == 'POST':
        form = ProductLinkForm(request.POST or None)
        if form.is_valid():
            title = form['title'].value()
            product, created = Product.objects.get_or_create(title=title,
                                                        data_source_id = ds_id)
            if created:
                product.manufacturer = form['manufacturer'].value()
                product.brand_name = form['brand_name'].value()
                product.upc = form['upc'].value()
                product.size = form['size'].value()
                product.color = form['color'].value()
                product.save()
            if not ProductDocument.objects.filter(document=doc).exists():
                p = ProductDocument(product=product, document=doc)
                p.save()
            document_type = form['document_type'].value()
            if document_type != doc.document_type:
                doc.document_type = DocumentType.objects.get(pk=document_type)
                doc.save()
            return redirect('link_product_list', pk=doc.data_group.pk)
    return render(request, template_name,{'document': doc, 'form': form})

@login_required()
def detach_puc_from_product(request, pk):
    p = Product.objects.get(pk=pk)
    pp = ProductToPUC.objects.get(product=p)
    pp.delete()
    return redirect('product_detail', pk=p.pk)

@login_required()
def bulk_assign_puc_to_product(request, template_name=('product_curation/'
                                                      'bulk_product_puc.html')):
    q = safestring.mark_safe(request.GET.get('q', ''))
    if q > '':
        p = (Product.objects.exclude(id__in=(ProductToPUC.objects.values_list('product_id', flat=True))).
                filter(title__icontains=q)|
                Product.objects.exclude(id__in=(ProductToPUC.objects.values_list('product_id', flat=True))).
                filter(brand_name__icontains=q))[:50]
    else:
        p = {}
    form = ProductPUCForm(request.POST or None)
    if form.is_valid():
        puc = PUC.objects.get(id=form['puc'].value())
        product_ids = safestring.mark_safe(request.POST.get('id_pks', '')).split(",")
        for id in product_ids:
            product = Product.objects.get(id=id)
            producttopuc = ProductToPUC.objects.filter(product=product, classification_method='MA')
            if producttopuc.exists():
                producttopuc.delete()
            ProductToPUC.objects.create(PUC=puc, product=product, classification_method='MA',
                                    puc_assigned_time=timezone.now(), puc_assigned_usr=request.user)
    form = ProductPUCForm(None)
    form["puc"].label = 'PUC to Assign to Selected Products'
    return render(request, template_name, {'products': p, 'q': q, 'form': form})

@login_required()
def assign_puc_to_product(request, pk, template_name=('product_curation/'
                                                      'product_puc.html')):
    """Assign a PUC to a single product"""
    form = ProductPUCForm(request.POST or None)
    p = Product.objects.get(pk=pk)
    if form.is_valid():
        puc = PUC.objects.get(id=form['puc'].value())
        producttopuc = ProductToPUC.objects.filter(product=p, classification_method='MA')
        if producttopuc.exists():
            producttopuc.delete()
        ProductToPUC.objects.create(PUC=puc, product=p, classification_method='MA',
                                    puc_assigned_time=timezone.now(), puc_assigned_usr=request.user)
        referer = request.POST.get('referer') if request.POST.get('referer') else 'category_assignment'
        pk = p.id if referer == 'product_detail' else p.data_source.id
        return redirect(referer, pk=pk)
    form.referer = resolve(parse.urlparse(request.META['HTTP_REFERER']).path).url_name\
        if 'HTTP_REFERER' in request.META else 'category_assignment'
    form.referer_pk = p.id if form.referer == 'product_detail' else p.data_source.id
    return render(request, template_name,{'product': p, 'form': form})

@login_required()
def product_detail(request, pk, template_name=('product_curation/'
                                                'product_detail.html')):
    p = get_object_or_404(Product, pk=pk, )
    tagform = ProductTagForm(request.POST or None, instance=p)
    tagform['tags'].label = ''
    ptopuc = p.get_uber_product_to_puc()
    puc = p.get_uber_puc()
    if tagform.is_valid():
        tagform.save()
    docs = p.datadocument_set.order_by('-created_at')
    return render(request, template_name, {'product': p,
                                            'puc'   : puc,
                                            'ptopuc': ptopuc,
                                            'tagform'  : tagform,
                                            'docs'  : docs
                                            })

@login_required()
def product_update(request, pk, template_name=('product_curation/'
                                               'product_edit.html')):
    p = Product.objects.get(pk=pk)
    form = ProductForm(request.POST or None, instance=p)
    if form.is_valid():
        form.save()
        return redirect('product_detail', pk=p.pk)
    return render(request, template_name,{'product': p, 'form': form})

@login_required()
def product_delete(request, pk):
    p = Product.objects.get(pk=pk)
    p.delete()
    return redirect('product_curation')

@login_required()
def product_list(request, template_name=('product_curation/'
                                                'products.html')):
    product = Product.objects.all()
    data = {}
    data['object_list'] = product
    return render(request, template_name, data)
