from dal import autocomplete
from datetime import datetime
from django.shortcuts import redirect
from django.db.models import Count, Q

from django.utils import timezone
from django.forms import ModelForm, ModelChoiceField
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from dashboard.models import DataSource, DataGroup, DataDocument, Product, ProductDocument, PUC, ProductToPUC
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class ProductForm(ModelForm):
    required_css_class = 'required' # adds to label tag
    class Meta:
        model = Product
        fields = ['title', 'manufacturer', 'brand_name', 'upc', 'size', 'color']


class ProductPUCForm(ModelForm):
    puc = ModelChoiceField(
        queryset=PUC.objects.all(),
        label='Category',
        widget=autocomplete.ModelSelect2(
            url='puc-autocomplete',
            attrs={'data-minimum-input-length': 3,  })
    )

    class Meta:
        model = ProductToPUC
        fields = ['puc']


@login_required()
def product_curation_index(request, template_name='product_curation/product_curation_index.html'):
    # List of all data groups which have had at least 1 data
    # document matched to a registered record
    linked_products = Product.objects.filter(documents__in=DataDocument.objects.all())
    data_sources = DataSource.objects.annotate(uploaded=Count('datagroup__datadocument'))\
        .filter(uploaded__gt=0)
    # A separate queryset of data sources and their related products without PUCs assigned
    # Changed in issue 232. Instead of filtering products based on their prod_cat being null,
    #   we now exclude all products that have a product_id contained in the ProductToPUC object set
    qs_no_puc = Product.objects.values('data_source').exclude(id__in=(ProductToPUC.objects.values_list('product_id', flat=True))).\
        filter(data_source__isnull=False).annotate(no_category=Count('id')).order_by('data_source')

    #qs_no_puc = Product.objects.values('data_source').filter(prod_cat__isnull=True).\
    #    filter(data_source__isnull=False).annotate(no_category=Count('id')).order_by('data_source')
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
    form = ProductForm(initial={'upc': upc_stub})
    if request.method == 'POST':
        form = ProductForm(request.POST or None)
        if form.is_valid():
            title = form['title'].value()
            brand_name = form['brand_name'].value()
            manufacturer = form['manufacturer'].value()
            upc_stub = form['upc'].value()
            try:
                product = Product.objects.get(title=title)
            except Product.DoesNotExist:
                now = timezone.now()
                product = Product.objects.create(title=title,
                                                 manufacturer=manufacturer,
                                                 brand_name=brand_name,
                                                 upc=upc_stub,
                                                 data_source_id=ds_id)
            p = ProductDocument(product=product, document=doc)
            p.save()
            return redirect('link_product_list', pk=doc.data_group.pk)
    return render(request, template_name,{'document': doc, 'form': form})

@login_required()
def assign_puc_to_product(request, pk, template_name=('product_curation/'
                                                      'product_puc.html')):
    """Assign a PUC to a single product"""
    form = ProductPUCForm(request.POST or None)
    p = Product.objects.get(pk=pk)
    if form.is_valid():
        puc = PUC.objects.get(id=form['puc'].value())
        new_product_to_puc = ProductToPUC.objects.create(PUC=puc, product=p, classification_method='MA',
                                                         puc_assigned_time=datetime.now(), puc_assigned_usr=request.user)
        new_product_to_puc.save()
        return redirect('category_assignment', pk=p.data_source.id)
    return render(request, template_name,{'product': p, 'form': form})

@login_required()
def product_detail(request, pk, template_name=('product_curation/'
                                                'product_detail.html')):
    p = get_object_or_404(Product, pk=pk, )
    ptopuc = p.get_uber_product_to_puc()
    puc = p.get_uber_puc()
    return render(request, template_name, {'product': p, 'puc': puc, 'ptopuc': ptopuc, })

@login_required()
def product_list(request, template_name=('product_curation/'
                                                'products.html')):
    product = Product.objects.all()
    data = {}
    data['object_list'] = product
    return render(request, template_name, data)
