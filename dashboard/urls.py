from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

import dashboard.views.qa
from . import views

urlpatterns = [
    path('', views.index,                   name='index'),
    path('datasources/', views.data_source_list,
                                            name='data_source_list'),
    path('datasource/<int:pk>', views.data_source_detail,
                                            name='data_source_detail'),
    path('datasource/new/', views.data_source_create,
                                            name='data_source_new'),
    path('datasource/edit/<int:pk>/', views.data_source_update,
                                            name='data_source_edit'),
    path('datasource/delete/<int:pk>/', views.data_source_delete,
                                            name='data_source_delete'),
    path('datagroups/', views.data_group_list,
                                            name='data_group_list'),
    path('datagroup/<int:pk>/', views.data_group_detail,
                                            name='data_group_detail'),
    path('datagroup/docs_csv/<int:pk>/', views.dg_dd_csv_view,
                                            name='dg_dd_csv_view'),
    path('datagroup/pdfs_zipped/<int:pk>/', views.dg_pdfs_zip_view,
                                            name='dg_pdfs_zip_view'),
    path('datagroup/raw_extracted_records/<int:pk>/', views.dg_raw_extracted_records,
                                            name='dg_raw_extracted_records'),
    path('datasource/<int:pk>/datagroup_new/', views.data_group_create,
                                            name='data_group_new'),
    path('datagroup/<int:pk>/registered_records.csv', views.data_group_registered_records_csv,
                                            name="registered_records.csv"),
    path('datagroup/edit/<int:pk>/', views.data_group_update,
                                            name='data_group_edit'),
    path('datagroup/delete/<int:pk>/', views.data_group_delete,
                                            name='data_group_delete'),
    path('datadocument/delete/<int:pk>/', views.data_document_delete,
                                            name='data_document_delete'),
    path('datadocument/note/<int:pk>/', views.data_document_note,
                                            name='data_document_note'),
    path('product_curation/', views.product_curation_index,
                                            name='product_curation'),
    path('chemical_curation/', views.chemical_curation_index,
         name='chemical_curation'),
    path('category_assignment/<int:pk>/', views.category_assignment,
                                            name='category_assignment'),
    path('link_product_list/<int:pk>/', views.link_product_list,
                                            name='link_product_list'),
    path('link_product_form/<int:pk>/', views.link_product_form,
                                            name='link_product_form'),
    path('qa/extractionscript/', views.qa_extractionscript_index,
                                            name='qa_extractionscript_index'),
    path('qa/extractionscript/<int:pk>/', dashboard.views.qa.qa_extraction_script,
                                            name='qa_extraction_script'),
    path('qa/extractedtext/<int:pk>/', dashboard.views.qa.extracted_text_qa,
                                            name='extracted_text_qa'),
    path('extractionscript/<int:pk>/', views.extraction_script_detail,
                                            name='extraction_script_detail'),
    path('qa/chemicalpresence/', views.qa_chemicalpresence_index,
                                            name='qa_chemicalpresence_index'),
    path('qa/chemicalpresencegroup/<int:pk>/', views.qa_chemicalpresence_group,
                                            name='qa_chemical_presence_group'),
    path('bulk_product_puc/', views.bulk_assign_puc_to_product,
                                            name='bulk_product_puc'),
    path('bulk_product_tag/', views.bulk_assign_tag_to_products,
                                            name='bulk_product_tag'),
    path('category_assignment/<int:ds_pk>/product_puc/<int:pk>',
                                            views.category_assign_puc_to_product,
                                            name='category_assignment_product_puc'),
    path('product_puc/<int:pk>/', views.product_assign_puc_to_product,
                                            name='product_puc'),
    path('product_puc_delete/<int:pk>/', views.detach_puc_from_product,
                                            name='product_puc_delete'),
    path('puc-autocomplete/', views.puc_autocomplete.PUCAutocomplete.as_view(),
                                            name='puc-autocomplete'),
    path('product/<int:pk>/', views.product_detail,
                                            name='product_detail'),
    path('product/edit/<int:pk>/', views.product_update,
                                            name='product_edit'),
    path('product/delete/<int:pk>/', views.product_delete,
                                            name='product_delete'),
    path('products/', views.product_list,  name='product_list'),
    path('datadocument/<int:pk>/', views.data_document_detail,
                                            name='data_document'),
    path('save_type/<int:pk>/', views.save_doc_form,
                                            name='save_doc_form'),
    path('save_ext/<int:pk>/', views.save_ext_form,
                                            name='save_ext_form'),
    path('save_list_presence_tags/<int:pk>/', views.save_list_presence_tag_form,
                                            name='save_list_presence_tag_form'),
    path('list_presence_tags_autocomplete/', views.list_presence_tag_autocomplete.ListPresenceTagAutocomplete.as_view(),
                                            name='list_presence_tags_autocomplete'),
    path('search/', include('haystack.urls')),
    path('find/', views.search.FacetedSearchView.as_view(),
                                            name='haystack_search'),
    path('p_json/', views.product_ajax,     name='p_ajax_url'),
    path('pucs/', views.puc_list,           name='puc_list'),
    path('puc/<int:pk>/', views.puc_detail, name='puc_detail'),
    path('dl_pucs/', views.download_PUCs,   name='download_PUCs'),
    path('dl_puctags/', views.download_PUCTags,   name='download_PUCTags'),
    path('dl_raw_chems/', views.download_raw_chems,  
                                            name='download_raw_chems'),
    path('dsstox/<str:sid>/', views.dsstox_lookup_detail,
                                            name='dsstox_lookup'),
    path('habitsandpractices/<int:pk>/', views.habitsandpractices,
                                            name='habitsandpractices'),
    path('link_habitandpractice_to_puc/<int:pk>/', views.link_habitsandpractices,
                                            name='link_habitsandpractices'),
    path('get_data/', views.get_data,      name='get_data'),
    path('dl_chem_summary/', views.download_chem_stats,
                                            name='download_chem_stats'),
    path('upload/dtxsid_csv/', views.upload_dtxsid_csv,
                                            name='upload_dtxsid_csv'),
    path('get_data/get_dsstox_csv_template/', views.get_data_dsstox_csv_template,
                                            name='get_data_dsstox_csv_template'),
    path('datagroup/diagnostics/<int:pk>/',   views.data_group_diagnostics,
                                            name='data_group_diagnostics'),
    path('datagroup/diagnostics/',          views.data_group_diagnostics,
                                            name='data_group_diagnostics'),
    path('extractedtext/edit/<int:pk>/',   views.extracted_text_edit,
                                            name='extracted_text_edit'),
    path('extractedchild/edit/<int:pk>/',   views.extracted_child_edit,
                                            name='extracted_child_edit'),
    path('datadocument/edit/<int:pk>/',   views.data_document_edit,
                                            name='data_document_edit'),
    path('qanotes/save/<int:pk>/',   views.save_qa_notes,
                                            name='save_qa_notes'),
    path('extractedtext/approve/<int:pk>/',   views.approve_extracted_text,
                                            name='approve_extracted_text'),
    path('search/es_chemicals/', views.search_chemicals,
                                            name='search_chemicals'),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
