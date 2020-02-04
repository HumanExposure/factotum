from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from dashboard.models import (
    ExtractedText,
    ExtractedChemical,
    ExtractedHabitsAndPractices,
    ExtractedListPresence,
    ExtractedHHRec,
    ExtractedFunctionalUse,
    DataGroup,
    DataSource,
    Script,
    GroupType,
    DataDocument,
    DocumentType,
    PUCTag,
    Product,
    PUC,
    ProductDocument,
    UnitType,
    WeightFractionType,
    ExtractedHabitsAndPracticesDataType,
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

fixtures_standard = [
    "00_superuser",
    "01_lookups",
    "02_datasource",
    "03_datagroup",
    "04_PUC",
    "05_product",
    "06_datadocument",
    "07_extractedtext",
    "07b_extractedcpcat",
    "07c_extractedhhdoc",
    "07d_rawchem",
    "07e_extractedchemical",
    "07f_extractedfunctionaluse",
    "07g_extractedlistpresence",
    "07h_extractedhhrec",
    "08_script",
    "09_productdocument",
    "10_habits_and_practices",
    "11_habits_and_practices_to_puc",
    "12_product_to_puc",
    "13_puc_tag",
    "14_list_presence_tag",
    "15_list_presence_to_tag",
    "17_taxonomy",
]

datadocument_models = {
    "CO": ExtractedChemical,
    "FU": ExtractedFunctionalUse,
    "HP": ExtractedHabitsAndPractices,
    "CP": ExtractedListPresence,
    "HH": ExtractedHHRec,
}


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def load_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    if settings.TEST_BROWSER == "firefox":
        return webdriver.Firefox()
    else:
        return webdriver.Chrome(
            executable_path=settings.CHROMEDRIVER_PATH, chrome_options=chrome_options
        )


def load_model_objects():
    user = User.objects.create_user(username="Karyn", password="specialP@55word")
    superuser = User.objects.create_superuser(
        username="SuperKaryn", password="specialP@55word", email="me@epa.gov"
    )
    ds = DataSource.objects.create(
        title="Data Source for Test", estimated_records=2, state="AT", priority="HI"
    )
    script = Script.objects.create(
        title="Test Download Script",
        url="http://www.epa.gov/",
        qa_begun=False,
        script_type="DL",
    )
    exscript = Script.objects.create(
        title="Test Extraction Script",
        url="http://www.epa.gov/",
        qa_begun=False,
        script_type="EX",
    )
    gt = GroupType.objects.create(title="Composition", code="CO")
    dg = DataGroup.objects.create(
        name="Data Group for Test",
        description="Testing...",
        data_source=ds,
        download_script=script,
        downloaded_by=user,
        downloaded_at=timezone.now(),
        group_type=gt,
        csv="register_records_matching.csv",
        url="https://www.epa.gov",
    )
    dt = DocumentType.objects.create(title="MSDS", code="MS")

    doc = DataDocument.objects.create(
        title="test document", data_group=dg, document_type=dt, filename="example.pdf"
    )
    p = Product.objects.create(upc="Test UPC for ProductToPUC")

    puc = PUC.objects.create(
        gen_cat="Test General Category",
        prod_fam="Test Product Family",
        prod_type="Test Product Type",
        description="Test Product Description",
        last_edited_by=user,
        kind="FO",
    )

    extext = ExtractedText.objects.create(
        prod_name="Test Extracted Text Record",
        data_document=doc,
        extraction_script=exscript,
    )
    ut = UnitType.objects.create(title="percent composition")
    wft = WeightFractionType.objects.create(title="reported", description="reported")
    ec = ExtractedChemical.objects.create(
        extracted_text=extext,
        unit_type=ut,
        weight_fraction_type=wft,
        raw_chem_name="Test Chem Name",
        raw_cas="test_cas",
        lower_wf_analysis=0.123456789012345,
        central_wf_analysis=0.2,
        upper_wf_analysis=1,
        script=script,
    )
    rc = ec.rawchem_ptr

    pt = PUCTag.objects.create(
        name="Test PUC Attribute", definition="I'd really like to be defined."
    )
    pd = ProductDocument.objects.create(product=p, document=doc)
    ehp_dt = ExtractedHabitsAndPracticesDataType.objects.create(
        title="Test Data Type", description="Test Description"
    )
    ehp = ExtractedHabitsAndPractices.objects.create(
        extracted_text=extext,
        product_surveyed="Test Product Surveyed",
        prevalence="Continuous",
        data_type=ehp_dt,
    )

    return dotdict(
        {
            "user": user,
            "superuser": superuser,
            "ds": ds,
            "script": script,
            "exscript": exscript,
            "dg": dg,
            "doc": doc,
            "p": p,
            "puc": puc,
            "extext": extext,
            "ut": ut,
            "wft": wft,
            "rc": rc,
            "ec": ec,
            "pt": pt,
            "pd": pd,
            "dt": dt,
            "gt": gt,
            "ehp_dt": ehp_dt,
            "ehp": ehp,
        }
    )
