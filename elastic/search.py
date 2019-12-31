from elasticsearch_dsl import A, Search
from elasticsearch_dsl.query import MultiMatch
import re

from django.conf import settings
from django.core.paginator import Paginator
from django.utils import html

FIELD_DICT = {
    "truechem_dtxsid": (
        "rawchem_cas",
        "rawchem_name",
        "truechem_dtxsid",
        "truechem_cas",
        "truechem_name",
    ),
    "puc_id": (
        "rawchem_cas^4",
        "rawchem_name^4",
        "truechem_dtxsid^4",
        "truechem_cas^4",
        "truechem_name^5",
        "puc_kind",
        "puc_gencat",
        "puc_prodfam",
        "puc_prodtype",
        "puc_description",
    ),
    "product_id": (
        "rawchem_cas^4",
        "rawchem_name^4",
        "truechem_dtxsid^4",
        "truechem_cas^5",
        "truechem_name^5",
        "product_upc",
        "product_manufacturer",
        "product_brandname",
        "product_title",
        "product_shortdescription",
        "product_longdescription",
    ),
    "datadocument_id": (
        "rawchem_cas^4",
        "rawchem_name^4",
        "truechem_dtxsid^4",
        "truechem_cas^5",
        "truechem_name^5",
        "datadocument_grouptype",
        "datadocument_title",
        "datadocument_subtitle",
    ),
}

FACETS = (
    "datadocument_grouptype",
    "puc_kind",
    "product_brandname",
    "product_manufacturer",
    "puc_gencatfacet",
)

FRIENDLY_FIELDS = {
    "@timestamp": "Last updated at",
    "rawchem_id": "ID",
    "rawchem_cas": "Raw chemical CAS",
    "rawchem_name": "Raw chemical name",
    "truechem_dtxsid": "True chemical DTXSID",
    "truechem_cas": "True chemical CAS",
    "truechem_name": "True chemical name",
    "datadocument_id": "ID",
    "datadocument_grouptype": "Group type",
    "datadocument_title": "Title",
    "datadocument_subtitle": "Subtitle",
    "product_id": "ID",
    "product_upc": "UPC",
    "product_manufacturer": "Manufacturer",
    "product_brandname": "Brand name",
    "product_title": "Title",
    "product_shortdescription": "Summary",
    "product_longdescription": "Description",
    "puc_id": "ID",
    "puc_kind": "Kind",
    "puc_gencat": "General category",
    "puc_gencatfacet": "General category",
    "puc_prodfam": "Product family",
    "puc_prodtype": "Product type",
    "puc_description": "Description",
}

VALID_MODELS = {"product", "datadocument", "puc", "chemical"}

TOTAL_COUNT_AGG = "unique_total_count"


class ElasticPaginator:
    """To be used with Django's paginator"""

    def __init__(self, length, q, model, facets={}, fuzzy=False, connection="default"):
        self.run_query = lambda size, offset: run_query(
            q, model, size, offset, facets, fuzzy, connection
        )
        self.length = length

    def __len__(self):
        return self.length

    def __getitem__(self, s):
        if type(s) == slice:
            offset = s.start if s.start is not None else 0
            end = s.stop if s.stop is not None else self.length + 1
            size = end - offset
            result = self.run_query(size, offset)["hits"]
            self.patch(result)
            return result

        else:
            offset = s
            size = 1
            result = self.run_query(size, offset)["hits"]
            self.patch(result)
            return result[0]

    def patch(self, result):
        # see if chemical matched
        chemfields = set(FIELD_DICT["truechem_dtxsid"])
        for hit in result:
            if chemfields & hit["highlights"].keys():
                hit["chemsearch"] = True
            else:
                hit["chemsearch"] = False
        # patch html
        for hit in result:
            for source_field, highlights in hit["highlights"].items():
                for hightlight in highlights:
                    stripped_highlight = re.escape(
                        re.sub(r"(<em>)|(</em>)", "", hightlight)
                    )
                    original_field = hit["source"][source_field]
                    hit["source"][source_field] = html.mark_safe(
                        re.sub(stripped_highlight, hightlight, original_field)
                    )
        # patch friendly name
        for hit in result:
            for source_field in hit["highlights"]:
                if source_field in FRIENDLY_FIELDS:
                    friendly = FRIENDLY_FIELDS[source_field]
                    hit["highlights"][friendly] = hit["highlights"].pop(source_field)
        return result


def run_query(
    q, model, size, offset=0, facets={}, fuzzy=False, connection="default", page=None
):
    """Run an Elasticsearch query.

    Arguments:
        q (str): the string to search
        model (str): one of 'chem', 'puc', 'product', or 'datadocument'
        size (int): the number of objects to return
        offset (optional int): the value to start at [default=0]
        page (optional int): the Django paginator page to return [default=None]
        facets (optional dict): a key, value pair to filter on. value can be a str or a list of strings 

            [default={}] e.g. {'datadocument_grouptype': 'CO'} or 
            {'datadocument_grouptype': ['CO', 'FU']}
        fuzzy (optional bool): enable fuzzy search [default=False]
        connection (optional str): which Elasticsearch instance to use [default="default"]

    Returns:
        {
        'hits': a list of results,
        'facets': a dictionary of facets,
        'took': time in seconds of search,
        'total': total results found
        }

    """
    # make sure the model is valid
    validate_model(model)
    # get index to search on based on ELASTICSEARCH setting and con
    index = settings.ELASTICSEARCH.get(connection, {}).get("INDEX", "_all")
    # get the search object
    s = Search(using=connection, index=index)
    # filter on the facets
    for term, filter_array in facets.items():
        s = s.filter("terms", **{term: filter_array})
    # pull relevant fields
    id_field = get_id_field(model)
    fields = FIELD_DICT[id_field]
    # filter null id
    s = s.filter("exists", field=id_field)
    # Enable highlighting
    s = s.highlight_options(order="score")
    s = s.highlight("*")
    # add the query with optional fuzziness
    if fuzzy:
        s = s.query(
            MultiMatch(query=q, fields=fields, type="most_fields", fuzziness="AUTO")
        )
    else:
        s = s.query(MultiMatch(query=q, fields=fields, type="most_fields"))
    # collapse on id_field
    dict_update = {}
    inner_hits = []
    for f in list(FIELD_DICT.keys()) + ["rawchem_id"]:
        inner_hits.append({"name": f, "collapse": {"field": f}, "size": 0})
    dict_update.update({"collapse": {"field": id_field, "inner_hits": inner_hits}})
    # set the size of the result
    if page is not None:
        dict_update.update({"size": 0, "from": 0})
    else:
        dict_update.update({"size": size, "from": offset})
    s.update_from_dict(dict_update)
    # aggregate facets
    for facet in FACETS:
        a = A("terms", field=facet)
        a.metric("unique_count", "cardinality", field=id_field)
        s.aggs.bucket(facet, a)
    # add cardinal aggregation on id_field to get unique total count
    s.aggs.bucket(TOTAL_COUNT_AGG, A("cardinality", field=id_field))
    # execute the search
    response = s.execute().to_dict()
    # gather the results
    # hits
    results_hits = []
    for h in response["hits"]["hits"]:
        results_hits_object = {
            "id": h["_source"][id_field],
            "num_rawchem": h["inner_hits"]["rawchem_id"]["hits"]["total"]["value"],
            "num_truechem": h["inner_hits"]["truechem_dtxsid"]["hits"]["total"][
                "value"
            ],
            "num_datadocument": h["inner_hits"]["datadocument_id"]["hits"]["total"][
                "value"
            ],
            "num_product": h["inner_hits"]["product_id"]["hits"]["total"]["value"],
            "num_puc": h["inner_hits"]["puc_id"]["hits"]["total"]["value"],
            "highlights": h["highlight"],
            "source": h["_source"],
        }
        results_hits.append(results_hits_object)
    # available facets
    results_facets = {}
    response_aggs = response["aggregations"]
    for facet in FACETS:
        results_facets_data = response_aggs[facet]
        results_facets_list = []
        for b in results_facets_data["buckets"]:
            results_facets_object = {
                "key": b["key"],
                "count": b["unique_count"]["value"],
            }
            results_facets_list.append(results_facets_object)
        results_facets[facet] = results_facets_list
    # get unique total count
    length = response_aggs[TOTAL_COUNT_AGG]["value"]
    # replace hits with paginator
    if page is not None:
        espaginator = ElasticPaginator(
            length, q, model, facets, fuzzy, connection="default"
        )
        results_hits = Paginator(espaginator, size).get_page(page)
    return {
        "hits": results_hits,
        "facets": results_facets,
        "took": response["took"] / 1000,
        "total": length,
    }


def get_unique_count(q, model, fuzzy=False, connection="default"):
    # make sure the model is valid
    validate_model(model)

    # get index to search on based on ELASTICSEARCH setting and con
    index = settings.ELASTICSEARCH.get(connection, {}).get("INDEX", "_all")
    # get the search object
    s = Search(using=connection, index=index)
    # pull relevant fields
    id_field = get_id_field(model)

    fields = FIELD_DICT[id_field]
    # filter null id
    s = s.filter("exists", field=id_field)
    # add the query with optional fuzziness
    if fuzzy:
        s = s.query(MultiMatch(query=q, fields=fields, fuzziness="AUTO"))
    else:
        s = s.query(MultiMatch(query=q, fields=fields))

    # add cardinal aggregation on id_field to get unique total count
    s.aggs.bucket(TOTAL_COUNT_AGG, A("cardinality", field=id_field))
    # execute the search
    response = s.execute().to_dict()
    # get unique total count
    response_aggs = response["aggregations"]
    return response_aggs[TOTAL_COUNT_AGG]["value"]


def validate_model(model):
    if model not in VALID_MODELS:
        raise ValueError("'model' must be one of " + str(valid_models))


def get_id_field(model):
    return model + "_id" if model != "chemical" else "truechem_dtxsid"
