/////////////////////
// API description //
/////////////////////
local description = |||
  The Factotum Web Services API is a service that provides data about Product Usage Category (PUC), consumer products, and the chemicals related to PUCs and products.

  ### OpenAPI
  This documentation is generated via the [OpenAPI specification](https://swagger.io/specification/) downloadable above. You can use this specification to assist in developing apps and using the API. For example, [Postman can import the OpenAPI specification](https://learning.postman.com/docs/postman/collections/working-with-openAPI/) to automatically build collections.

  ### JSON:API
  Endpoints are being changed to follow the [JSON:API specification](https://jsonapi.org/).
|||;


///////////////////
// Import models //
///////////////////

local chemical  = import 'dashboard/chemical.libsonnet';
local chemicalInstance  = import 'dashboard/chemicalInstance.libsonnet';
local chemical_presence = import 'dashboard/chemical_presence.libsonnet';
local composition = import 'dashboard/composition.libsonnet';
local dataDocument  = import 'dashboard/dataDocument.libsonnet';
local dataGroup = import 'dashboard/dataGroup.libsonnet';
local dataSource = import 'dashboard/dataSource.libsonnet';
local functional_use  = import 'dashboard/functionalUse.libsonnet';
local functional_use_category = import 'dashboard/functionalUseCategory.libsonnet';
local product = import 'dashboard/product.libsonnet';
local puc = import 'dashboard/puc.libsonnet';
local classificationMethod = import 'dashboard/classificationMethod.libsonnet';

////////////////////////
// List of all models //
////////////////////////
local objs = [
    chemical,
    chemicalInstance,
    chemical_presence,
    classificationMethod,
    composition,
    dataDocument,
    dataGroup,
    dataSource,
    functional_use,
    functional_use_category,
    product,
    puc,
];

// Build spec
local jsonapi = import 'jsonapi.libsonnet';
jsonapi.buildSpec(objs, description)
