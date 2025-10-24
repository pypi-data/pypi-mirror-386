# API Feedback for Katana Development Team

This document provides systematic feedback on the Katana Public API based on extensive
client development, validation testing, and real-world usage patterns. These insights
come from building a production-ready Python client with comprehensive OpenAPI
specification analysis.

**Last Updated**: August 29, 2025 **Client Version**: v0.9.0 **API Endpoints Analyzed**:
76+ endpoints **Data Models Analyzed**: 207 schemas **Documentation Pages Analyzed**:
245 comprehensive pages from developer.katanamrp.com

**Validation Status**: OpenAPI schema validation completed with 6 remaining
discrepancies between external validation examples and actual API behavior (documented
below).

______________________________________________________________________

## 🔴 Critical Issues

### Response Code Inconsistencies for CREATE Operations

**Issue**: Katana API uses non-standard HTTP status codes for CREATE operations.

**Current Behavior**:

- **All CREATE endpoints return `200 OK`** instead of standard `201 Created`
- Verified across 245 comprehensive documentation pages from developer.katanamrp.com
- Consistent behavior: Every CREATE operation documented shows "200 Response"

**Examples**:

- `POST /customers` → Returns `200 OK`
- `POST /products` → Returns `200 OK`
- `POST /sales_orders` → Returns `200 OK`
- `POST /price_lists` → Returns `200 OK`
- `POST /webhooks` → Returns `200 OK`

**Impact**:

- **Standards Violation**: Violates HTTP/REST standards (RFC 7231 Section 6.3.2)
- **Developer Expectations**: Most REST APIs return `201 Created` for successful
  resource creation
- **Client Integration**: May confuse developers familiar with standard REST conventions
- **Semantic Clarity**: `200 OK` typically indicates successful processing, not resource
  creation

**Recommendation**:

- **Consider**: Migrate to `201 Created` for CREATE operations in future API version
- **Breaking Change**: Would require proper versioning and migration strategy
- **Industry Alignment**: Would align Katana API with REST standards and developer
  expectations
- **Benefit**: Better alignment with HTTP standards and developer expectations
- **Migration**: Could support both status codes during transition period
- **Documentation**: Update both OpenAPI spec and developer documentation
- **Breaking Change**: Document as API improvement with proper versioning

### BOM Row Creation Returns No Content

**Issue**: BOM row creation operations return `204 No Content` instead of created
resource data.

**Affected Endpoints**:

- `POST /bom_rows` (single) → Returns `204 No Content`
- `POST /bom_rows/batch` (bulk) → Returns `204 No Content`

**Critical Problems**:

1. **No Resource IDs**: Impossible to determine IDs of newly created BOM rows
1. **Non-Standard Behavior**: `204 No Content` typically indicates successful processing
   with no response body
1. **Integration Limitations**: Prevents immediate follow-up operations on created
   resources
1. **Workflow Disruption**: Forces additional API calls to retrieve created resource
   information
1. **Documentation Gap**: Success scenarios are completely undocumented

**Business Impact**:

- **Automated Workflows**: Cannot chain operations that depend on new BOM row IDs
- **Batch Operations**: No way to map bulk creation results to specific inputs
- **Error Handling**: Difficult to verify which specific rows were created successfully
- **Data Synchronization**: Prevents efficient sync operations with external systems
- **Developer Experience**: Lack of success documentation creates confusion

**Recommendation**:

- **Critical Fix**: Return created resource data with proper status codes
- **Single Creation**: Return `201 Created` with created BOM row object including
  generated ID
- **Bulk Creation**: Return `201 Created` with array of created BOM row objects
  including IDs
- **Documentation**: Add comprehensive success response examples to official
  documentation
- **Consistency**: Align with other CREATE endpoints that return resource data

### BOM Management Operations Severely Limited

**Issue**: BOM row management lacks essential bulk and ordering operations, requiring
excessive API calls for common workflows.

**Missing Critical Operations**:

1. **No Rank/Order Management**:

   - `PATCH /bom_rows/{id}` does not support updating `rank` field
   - Cannot reorder BOM rows efficiently
   - No dedicated reordering endpoints (unlike product operations which have
     `/product_operation_rerank`)
   - **API Inconsistency**: Product operations have reranking support, BOM rows do not

1. **No Bulk Operations**:

   - ❌ Bulk update: No `PATCH /bom_rows/batch` endpoint
   - ❌ Bulk delete: No `DELETE /bom_rows/batch` endpoint
   - ❌ Bulk replace: No `PUT /variants/{id}/bom_rows` to replace entire BOM

1. **Inefficient BOM Management**:

   - Updating BOM structure requires many individual API calls
   - No atomic operations for BOM modifications
   - No way to replace entire BOM in single request

**Common Workflow Impact**:

- **BOM Reordering**: Must delete and recreate rows or PATCH changes by rank order to
  change order
- **BOM Updates**: Each row requires separate PATCH request
- **BOM Replacement**: Must delete all rows, then create new ones individually
- **Recipe Management**: What should be simple recipe changes require dozens of API
  calls

**Business Impact**:

- **Performance**: Excessive API calls slow down BOM management operations
- **Reliability**: Multiple requests increase failure points and partial update risks
- **Rate Limiting**: High request volume may hit API rate limits
- **User Experience**: Slow response times for common manufacturing operations
- **Data Consistency**: No atomic operations risk leaving BOMs in inconsistent states

**Recommendation**:

- **Add Rank Support**: Enable rank field updates in `PATCH /bom_rows/{id}`
- **BOM Rerank Endpoint**: Add `POST /bom_row_rerank` endpoint similar to existing
  `/product_operation_rerank`
- **Bulk Operations**: Add endpoints for batch update, delete, and create operations:
  - `PATCH /bom_rows/batch` for bulk updates
  - `DELETE /bom_rows/batch` for bulk deletions
  - `PUT /variants/{id}/bom_rows` for atomic BOM replacement
- **Consistency**: Align BOM row management capabilities with product operation
  management
- **Atomic Operations**: Ensure BOM modifications can be done transactionally

### Documentation Accuracy Issues in Material Endpoints

**Issue**: Several inconsistencies and errors found in official API documentation during
comprehensive validation against OpenAPI specification.

**Source**: Comprehensive cross-validation of material endpoints against 245+ pages from
developer.katanamrp.com, completed August 2025.

**Documentation Errors Identified**:

1. **Copy-Paste Errors in Material Configuration Examples**:

   - **Location**: Material object documentation and config examples
   - **Error**: Shows `"product_id": 1` in material configuration objects
   - **Correct**: Should be `"material_id": 1` for material configurations
   - **Impact**: Developer confusion when implementing material management features

1. **Inconsistent Purchase UOM Examples**:

   - **Location**: Material creation and update endpoint documentation
   - **Error**: Examples show redundant purchase UOM conversion rates (e.g.,
     `purchase_uom: "kg"` with `purchase_uom_conversion_rate: 1.0`)
   - **Issue**: When purchase UOM equals inventory UOM, conversion rate should be
     null/omitted
   - **Correct Pattern**: `purchase_uom: null, purchase_uom_conversion_rate: null` when
     no conversion needed
   - **Impact**: Developers may implement unnecessary conversion logic

1. **Missing Conditional Requirements Documentation**:

   - **Location**: Material creation request documentation
   - **Gap**: Purchase UOM fields interdependency not clearly documented
   - **Business Rule**: `purchase_uom` and `purchase_uom_conversion_rate` must be
     provided together or both omitted
   - **Impact**: API integration errors due to incomplete validation requirements

1. **Field Constraint Inconsistencies**:

   - **Location**: Various material and variant endpoint examples
   - **Issue**: Documentation examples don't reflect actual field validation constraints
   - **Examples**:
     - `supplier_item_codes` constraints (1-40 characters per item) not documented
     - `registered_barcode` constraints (3-40 characters) not reflected in examples
     - `config_attributes` minimum requirements not specified
   - **Impact**: Client validation implementations may be too permissive or restrictive

**Validation Findings**:

- **OpenAPI Specification Accuracy**: Client's OpenAPI spec is more accurate than
  official documentation
- **Better Examples**: OpenAPI spec contains corrected examples that reflect actual API
  behavior
- **Proper Constraints**: OpenAPI spec includes comprehensive field validation that
  matches actual API requirements
- **Conditional Logic**: OpenAPI spec properly implements dependentRequired patterns for
  business rules

**Impact on Development**:

- **Integration Issues**: Developers following documentation examples may encounter API
  validation errors
- **Inconsistent Implementation**: Different teams may implement different
  interpretations
- **Support Burden**: Increased support requests due to documentation-reality mismatches
- **Development Velocity**: Slower development due to trial-and-error API integration

**Recommendation**:

- **Documentation Review**: Comprehensive audit of material endpoint documentation for
  accuracy
- **Example Correction**: Update all material configuration examples to use correct
  field names
- **Purchase UOM Clarity**: Clarify when purchase UOM conversion is needed vs. when to
  omit fields
- **Constraint Documentation**: Add comprehensive field validation documentation with
  examples
- **Cross-Validation**: Implement systematic validation between API implementation and
  documentation
- **Living Documentation**: Consider generating documentation from OpenAPI specification
  to ensure consistency

### Missing CREATE Endpoint - Storage Bins

**Issue**: No `POST /storage_bins` endpoint exists despite having update/delete
operations.

**Current CRUD Coverage**:

- ✅ GET `/storage_bins` (list)
- ✅ PATCH `/storage_bins/{id}` (update)
- ✅ DELETE `/storage_bins/{id}` (delete)
- ❌ POST `/storage_bins` (create) - **MISSING**

**Business Impact**:

- Prevents automated warehouse setup workflows
- Forces manual UI creation of storage locations
- Breaks CRUD completeness expectations
- Limits programmatic inventory management capabilities

**Recommendation**: Add `POST /storage_bins` endpoint with proper `201 Created`
response.

______________________________________________________________________

## 🟡 Documentation & Specification Issues

### Extend Parameter Documentation Gap

**Issue**: The `extend` query parameter is available on many endpoints but the valid
object names for each endpoint are not documented.

**Current Behavior**:

- Many endpoints support an `extend` parameter to include related objects in responses
- Parameter accepts a comma-separated list of object names to expand
- Valid object names vary by endpoint and resource type
- No documentation exists listing available extend options per endpoint

**Examples of Undocumented Extend Options**:

- `GET /products?extend=variants,bom_rows` - Works but variants/bom_rows not documented
  as valid options
- `GET /sales_orders?extend=customer,rows` - Available extends unknown without trial and
  error
- `GET /manufacturing_orders?extend=productions,recipe_rows` - Extend capabilities
  undiscovered

**Developer Impact**:

- **Trial and Error**: Developers must guess valid extend object names
- **Inefficient Discovery**: No systematic way to find all available relationships
- **Missed Optimization**: Developers may not use extend due to unclear documentation
- **Integration Delays**: Time spent testing which extend options work

**Business Impact**:

- **API Efficiency**: Extend parameter can reduce API calls significantly when used
  properly
- **Developer Experience**: Poor documentation discourages optimal API usage patterns
- **Performance**: Missed opportunities for single-request data retrieval

**Recommendation**:

- **Document All Extend Options**: List valid extend object names for each endpoint
- **Relationship Documentation**: Clearly document which related objects can be expanded
- **Examples**: Provide practical examples showing extend usage for common scenarios
- **API Reference**: Include extend options in endpoint documentation consistently

______________________________________________________________________

### Inconsistent Quantity Field Data Types

**Issue**: Quantity fields have inconsistent data types across different parts of the
API, mixing strings and numbers for similar concepts.

**Examples Found**:

**SalesReturnRow API Pattern**:

- **Main quantity field**: Returns string `"2.00"` (JSON string)
- **Batch transaction quantity**: Returns number `1` (JSON number)
- **Request schema**: Explicitly defines quantity as `type: "string"` in creation
  endpoints

**Evidence from API Documentation**:

- `POST /sales_return_rows` request schema: `"quantity": {"type": "string"}`
- `GET /sales_return_rows` response: `"quantity": "2.00"` (string)
- Same response, batch_transactions: `"quantity": 1` (number)

**Current Implementation Decision**:

- **Temporary Fix**: Updated OpenAPI schema to match API behavior (string type for main
  quantities)
- **Schema Updated**: SalesReturnRow.quantity changed to `type: string` with precision
  note

**Questions for Katana Team**:

1. **Design Intent**: Is the string format for main quantity fields intentional for
   decimal precision handling?

1. **Consistency Strategy**: Should all quantity fields across the API use consistent
   data types?

1. **Financial Precision**: Are string quantities specifically for financial/accounting
   precision vs. operational quantities?

1. **Future Direction**: Is this pattern expected to be standardized across other
   quantity fields in the API?

**Business Impact**:

- **Client Complexity**: Developers must handle mixed data types for similar concepts
- **Type Safety**: Generated clients may have inconsistent type definitions
- **Integration Confusion**: Unclear when to expect strings vs numbers for quantities

**Recommendation Options**:

1. **Standardize on Strings**: Use string format for all quantity fields (best for
   precision)
1. **Standardize on Numbers**: Use number format for all quantity fields (most common in
   APIs)
1. **Document Pattern**: Clearly document when to use strings vs numbers for different
   quantity types
1. **Hybrid Approach**: Use strings for financial quantities, numbers for operational
   quantities

## 🔵 API Design & Consistency Improvements

### PATCH vs PUT Semantics

**Issue**: PATCH operations sometimes require fields that should be optional.

**Example**: `PATCH /storage_bins/{id}` spec shows `bin_name` and `location_id` as
required.

**REST Standard**: PATCH should allow partial updates with all fields optional.

**Recommendation**:

- Make all PATCH operation fields optional
- Consider adding PUT endpoints for full replacement operations
- Document partial update behavior clearly

### Webhook Payload Documentation Gaps

**Issue**: Webhook payload structure includes undocumented fields.

**Specific Finding**: Webhook examples show a `status` field in the event payload's
`object` property, but this field is not documented anywhere in the official API
documentation.

**Example Webhook Payload Structure**:

```json
{
  "resource_type": "sales_order",
  "action": "sales_order.delivered",
  "webhook_id": 123,
  "object": {
    "id": "12345",
    "status": "DELIVERED",  // ← This field is undocumented
    "href": "https://api.katanamrp.com/v1/sales_orders/12345"
  }
}
```

**Documentation Gap**:

- No specification of what values `status` can contain
- No indication of whether this field is always present
- Unknown if `status` values vary by resource type
- Unclear relationship between `status` and the actual resource state

**Business Impact**:

- Developers cannot rely on `status` field for automation
- Webhook integration requires additional API calls to get reliable status
- Increases development complexity and API usage

**Recommendation**:

- Document all fields present in webhook payloads
- Specify possible `status` values for each resource type
- Clarify the relationship between webhook `status` and resource state
- Consider removing undocumented fields or making them official

______________________________________________________________________

## 🟢 Feature Gaps & Enhancement Opportunities

### Bulk Operations Support

**Current State**: Limited bulk operations available, but not comprehensive across all
resource types.

**Available Bulk Operations**:

- `/bom_rows/batch/create` - Bulk creation of BOM (Bill of Materials) rows using
  `BatchCreateBomRowsRequest` schema

**Business Need**:

- Large integrations need efficient bulk operations
- Migration scenarios require bulk data transfer
- Inventory updates often involve hundreds of records

**Missing Operations**:

- Bulk product creation/updates
- Bulk inventory adjustments
- Bulk order processing
- Bulk customer/supplier import

**API Efficiency Issues**:

- Most resource types still require individual API calls for creation/updates
- BOM row management has some bulk support but other related resources (products,
  variants) do not
- High-volume scenarios (product imports, customer imports) require careful rate
  limiting

**Recommendation**:

- Add bulk endpoints for high-volume operations beyond BOM rows
- Implement proper transaction handling for bulk operations
- Provide progress tracking for long-running bulk jobs
- Extend bulk support to products, variants, customers, and inventory adjustments

### Authentication & Permission Granularity

**Questions**:

- Are there different API key permission levels?
- Can permissions be scoped to specific resources?
- How is multi-location/multi-company data isolation handled?

**Business Need**:

- Read-only keys for reporting systems
- Scoped keys for integration partners
- Audit trails for API access

## 📊 Rate Limiting & Performance

### Current Implementation

- 60 requests per 60 seconds
- Retry-After headers provided
- No apparent distinction between endpoint types

**Developer Feedback**: The current 60 requests per minute limitation has been
frustrating for production integrations, especially when combined with the lack of bulk
operations for most endpoints. Consider increasing limits while maintaining system
stability.

### Questions

- Do different endpoint categories have different limits?
- Are there separate limits for bulk operations?
- How are rate limits calculated for different API key tiers?

### Recommendations

- **Increase Rate Limits**: Consider raising from 60 to 120-300 requests per minute to
  reduce integration friction
- **Tiered Rate Limiting**: Implement higher limits for production API keys vs.
  development keys
- **Endpoint-Specific Limits**: Higher limits for read operations (GET) vs. write
  operations (POST/PATCH)
- **Bulk Operation Limits**: Separate, higher limits for bulk endpoints to encourage
  their use
- **Rate Limit Monitoring**: Provide dashboards for API usage monitoring and limit
  tracking
- **Documentation**: Clearly document rate limiting strategy and best practices

### Missing Pagination Parameters on Collection Endpoints

**Issue**: Some collection endpoints that return arrays of resources lack standard
pagination parameters, making it difficult to handle large datasets efficiently.

**Affected Endpoints**:

- `GET /serial_numbers_stock` - Returns array but no `limit`, `page`, or `offset`
  parameters
- `GET /custom_fields_collections` - Returns array but no pagination parameters

**Current Behavior**:

- These endpoints return all results in a single response
- No way to paginate through large result sets
- Potentially inefficient for large datasets
- Inconsistent with other collection endpoints that do support pagination

**Verification**: Both endpoints confirmed to lack pagination parameters in the official
API specification (checked against comprehensive documentation).

**Business Impact**:

- **Performance**: Large result sets may cause slow API responses
- **Memory Usage**: Clients must handle potentially large JSON payloads
- **User Experience**: No progressive loading possible for large datasets
- **Consistency**: Inconsistent API behavior compared to other collection endpoints

**Expected Collection Endpoint Patterns**:

Most collection endpoints support:

- `limit` - Maximum number of results per page
- `page` - Page number for pagination
- `offset` - Alternative pagination method
- Response metadata with pagination info

**Recommendation**:

- **Add Pagination Support**: Implement standard pagination parameters for these
  endpoints
- **Consistent Parameters**: Use same pagination parameter names as other endpoints
- **Response Metadata**: Include pagination metadata in responses (`total_count`,
  `page_info`, etc.)
- **Backward Compatibility**: Ensure changes don't break existing clients
- **Documentation**: Update API documentation to reflect pagination capabilities

### Inconsistent 204 No Content Responses

**Issue**: Several endpoints return `204 No Content` where they should return created
resource data or success information with content.

**Affected Endpoints**:

- `POST /manufacturing_order_unlink` - Returns `204 No Content`
- `POST /purchase_order_receive` - Returns `204 No Content`
- `POST /unlink_variant_bin_locations` - Returns `204 No Content`
- `POST /recipes` - Returns `204 No Content`
- `POST /bom_rows` - Returns `204 No Content` (documented above)
- `POST /bom_rows/batch/create` - Returns `204 No Content` (documented above)
- `POST /product_operation_rows` - Returns `204 No Content`

**Current Behavior**:

- These creation/action endpoints return no response body
- Client cannot determine success details or created resource information
- Forces additional API calls to verify operation results

**Problems**:

- **No Confirmation Data**: Impossible to get created resource IDs or operation details
- **Integration Challenges**: Difficult to chain operations that depend on results
- **Non-Standard Pattern**: Most REST APIs return created resources with `201 Created`
- **User Experience**: No immediate feedback on operation success details

**Business Impact**:

- **Workflow Disruption**: Cannot build efficient automated workflows
- **Additional API Calls**: Forced to make extra requests to verify results
- **Development Complexity**: Harder to build reliable integrations
- **Inconsistent API**: Mixed patterns confuse developers

**Recommendation**:

- **Return Resource Data**: Provide created/modified resource information in response
  body
- **Use 201 Created**: For creation operations, return appropriate success status with
  data
- **Consistent Patterns**: Align all similar operations to return useful response data
- **Documentation**: Update examples to show expected response formats

### Parameter Naming Inconsistencies

**Issue**: Related endpoints use different parameter names for the same concepts,
creating confusion and integration complexity.

**Examples of Inconsistent Naming**:

- **ID Parameters**: Some endpoints use `customer_id` while related endpoints use
  `customer_ids` (array)
- **Resource Filters**: Mixed patterns like `sales_order_id` vs `sales_order_ids` for
  filtering
- **Date Ranges**: Inconsistent use of `created_at_min/max` vs other date range patterns
- **Status Filters**: Some endpoints have `status` parameters while related endpoints
  lack them

**Current Impact**:

- **Developer Confusion**: Must check each endpoint's parameters individually
- **Integration Complexity**: Cannot reuse parameter handling logic across similar
  endpoints
- **Documentation Overhead**: Requires extensive parameter documentation per endpoint
- **Client Generation Issues**: Generated clients may have inconsistent method
  signatures

**Business Impact**:

- **Development Time**: Slower integration development due to parameter inconsistencies
- **Error Prone**: Easy to use wrong parameter names when switching between endpoints
- **Maintenance Burden**: Harder to maintain consistent client code

**Recommendation**:

- **Standardize Parameter Names**: Establish consistent naming conventions for common
  parameters
- **Resource ID Patterns**: Use consistent patterns for single vs. multiple resource IDs
- **Date Range Conventions**: Standardize date filtering parameter names across all
  endpoints
- **Documentation**: Create parameter naming guidelines for future endpoints

### Response Schema Documentation via References

**Issue**: Many endpoint responses use `$ref` references to shared response schemas
without providing endpoint-specific context or descriptions.

**Current Pattern**:

```yaml
responses:
  "401":
    $ref: "#/components/responses/UnauthorizedError"
  "422":
    $ref: "#/components/responses/UnprocessableEntityError"
```

**Problems**:

- **No Endpoint Context**: Generic error responses don't explain endpoint-specific error
  conditions
- **Limited Debugging Info**: Developers can't understand what specific validations
  might fail
- **Poor Developer Experience**: No guidance on how to handle errors for specific
  operations
- **Documentation Gaps**: OpenAPI documentation tools show generic descriptions only

**Business Impact**:

- **Integration Difficulty**: Developers struggle to handle errors appropriately
- **Support Burden**: More support requests due to unclear error handling
- **Development Delays**: Time spent figuring out endpoint-specific error conditions

**Recommendation**:

- **Add Endpoint-Specific Descriptions**: Provide context for how shared responses apply
  to each endpoint
- **Error Condition Examples**: Document specific validation failures for each endpoint
- **Hybrid Approach**: Use `$ref` for consistency but add endpoint-specific descriptions
- **Documentation**: Enhance error handling examples in API documentation

### Inconsistent Resource Pattern - Factory Endpoint

**Issue**: The `/factory` endpoint follows a singleton pattern that differs from other
resource endpoints, potentially causing confusion.

**Current Behavior**:

- `GET /factory` - Returns factory information (singleton resource)
- No `/factories` (plural) endpoint
- No individual factory ID-based endpoints like `/factories/{id}`

**Pattern Comparison**:

```yaml
# Standard Collection Pattern:
GET /customers      # List all customers
GET /customers/{id} # Get specific customer

# Factory Singleton Pattern:
GET /factory        # Get factory info (no collection)
```

**Potential Issues**:

- **Developer Expectations**: Most REST APIs use consistent collection patterns
- **Client Generation**: Code generators may handle singleton differently
- **Documentation Clarity**: Pattern inconsistency requires special documentation
- **Future Scaling**: Unclear how pattern would extend if multiple factories supported

**Current Assessment**: This appears to be a legitimate business requirement (single
factory per account), but the pattern inconsistency should be documented.

**Recommendation**:

- **Document Pattern**: Clearly explain why `/factory` uses singleton pattern
- **API Guidelines**: Document when singleton vs. collection patterns are appropriate
- **Client Examples**: Provide specific examples for singleton resource usage
- **Future Planning**: Consider how pattern would evolve for multi-factory scenarios

______________________________________________________________________

## 🟠 Schema Validation Discrepancies

### Mixed Amount Field Data Types Across API

**Issue**: The Katana API uses inconsistent data types for monetary amount fields,
mixing strings and numbers across different endpoints and contexts.

**Validation Source**: Comprehensive schema validation performed August 29, 2025,
comparing external API examples against actual API responses and our OpenAPI 3.1
specification.

#### Confirmed Actual API Behavior (From Real Response Data)

**Shipping Fee Amounts - Always Strings**:

```json
// Actual API Response - shipping_fee objects
"shipping_fee": {
  "id": 4933554,
  "sales_order_id": 33066353,
  "description": "Shipping",
  "amount": "7.8500000000",    // STRING with 10 decimal places
  "tax_rate_id": 402909
}
```

**Sales Order Row Amounts - Always Strings**:

```json
// Actual API Response - sales_order_rows objects
"sales_order_rows": [{
  "price_per_unit": "4599.0000000000",      // STRING with 10 decimal places
  "total_discount": "0.0000000000",         // STRING with 10 decimal places
  "price_per_unit_in_base_currency": 4599,  // NUMBER (integer)
  "total": 4599,                           // NUMBER (integer)
  "total_in_base_currency": 4599           // NUMBER (integer)
}]
```

**Sales Order Main Amounts - Always Numbers**:

```json
// Actual API Response - sales order object
{
  "total": 4943.925,                    // NUMBER (decimal)
  "total_in_base_currency": 4943.925,   // NUMBER (decimal)
  "conversion_rate": 1                  // NUMBER (integer)
}
```

#### External Validation Example Discrepancies

**Problem**: External validation examples (from downloaded API spec) show **numeric
values** (`3.14`, `0`) for shipping fee amounts, but **actual API consistently returns
string values** like `"7.8500000000"`.

**Schema Decision**: Our OpenAPI specification correctly uses `type: string` for
`SalesOrderShippingFee.amount` to match actual API behavior.

#### Current Validation Errors (6 remaining)

These validation errors occur because external validation examples don't match actual
API format:

1. **bin_locations** - External data uses `name` vs our schema expects `bin_name` ✅
   **Our schema correct**
1. **manufacturing_order_operation_rows** - External data wrapped in response objects vs
   direct objects ✅ **Our schema correct**
1. **sales_order_shipping_fee endpoints** - External examples show numbers (`3.14`) vs
   actual API strings (`"7.8500000000"`) ✅ **Our schema correct**
1. **stock_transfers status** - External data wrapped in response objects vs direct
   objects ✅ **Our schema correct**

#### Impact on Client Development

**Positive**: Our OpenAPI schema accurately reflects actual API behavior

- ✅ Generated clients correctly handle string amounts for shipping fees
- ✅ Generated clients correctly handle number amounts for order totals
- ✅ Type safety matches real API responses

**Complexity**: Developers must handle mixed data types

- Mixed string/number amounts require careful client-side handling
- Financial calculations need decimal precision considerations
- Different serialization patterns across related endpoints

#### Questions for Katana Team

1. **Design Rationale**: Is the string format intentional for high-precision monetary
   fields (`price_per_unit`, `amount`)?

1. **Precision Requirements**: Are 10-decimal-place strings needed for accounting
   precision vs standard 2-decimal currency handling?

1. **Consistency Strategy**: Would standardizing on either all-string or all-number
   amounts be considered for future API versions?

1. **External Examples**: Can the external validation examples be updated to match
   actual API behavior?

#### Recommendations

**For Katana API Team**:

- **Documentation**: Clearly document the mixed data type strategy and precision
  requirements
- **Validation Examples**: Update external API examples to match actual API response
  formats
- **Consistency**: Consider long-term strategy for amount field data types across all
  endpoints

**For Client Developers**:

- Our OpenAPI specification correctly handles the actual API behavior
- Use string-based decimal libraries for financial calculations involving
  `price_per_unit` and shipping `amount` fields
- Handle mixed types appropriately in client applications

### Storage Bin Field Name Discrepancy

**Issue**: External validation examples use `name` field while actual API specification
expects `bin_name`.

**Status**: ✅ **Our schema is correct** - this is an external example data issue, not a
schema problem.

**Details**: Our StorageBin schema correctly requires `bin_name` field, matching the
actual API specification and business logic.

### Manufacturing Order Operation Response Structure

**Issue**: External validation examples wrap response data in container objects while
our schema expects direct object responses.

**Status**: ✅ **Our schema is correct** - this reflects proper REST API response
structure expectations.

**Details**: Our ManufacturingOrderOperationRow schema correctly expects direct object
responses with `id` as a required property, not wrapped in additional container objects.

### Stock Transfer Status Response Structure

**Issue**: External validation examples wrap response data in `example` container
objects while our schema expects direct StockTransfer objects.

**Status**: ✅ **Our schema is correct** - this matches standard REST API response
patterns.

**Details**: Our StockTransfer schema correctly expects direct object responses with
proper required fields, not wrapped in additional container structures.

### Empty Array Rejection on Update Operations

**Issue**: Some update operations reject empty arrays and require fields to be omitted
entirely if no values are being set.

**Affected Fields**:

- **UpdateProductRequest.configs**: Cannot send `configs: []` - must omit field entirely
  or send array with `minItems: 1`
- **UpdateMaterialRequest.configs**: Cannot send `configs: []` - must omit field
  entirely or send array with `minItems: 1`
- Potentially other array fields in update operations (not yet fully cataloged)

**Current Behavior**:

```json
// ❌ REJECTED - Empty array not allowed
{
  "name": "Updated Product",
  "configs": []
}

// ✅ ACCEPTED - Field omitted
{
  "name": "Updated Product"
}

// ✅ ACCEPTED - Non-empty array
{
  "name": "Updated Product",
  "configs": [
    {
      "name": "Size",
      "values": ["Small", "Medium", "Large"]
    }
  ]
}
```

**API Behavior**:

- Sending empty array results in validation error (422 Unprocessable Entity)
- API requires either:
  1. Omit the field entirely (preserves existing values)
  1. Send non-empty array with at least 1 item (updates/replaces values)

**OpenAPI Specification Fix**:

- Added `minItems: 1` constraint to UpdateProductRequest.configs
- Added `minItems: 1` constraint to UpdateMaterialRequest.configs
- Added documentation explaining the "omit vs empty" requirement

**Client Impact**:

- Developers must filter out empty arrays before sending requests
- Cannot use empty array to "clear all" - must delete related resources first
- Pattern example:
  ```python
  # Filter out empty configs array - API requires at least 1 item if configs is sent
  updates = {"name": "Product", "configs": []}
  filtered = {k: v for k, v in updates.items()
              if not (k == "configs" and isinstance(v, list) and len(v) == 0)}
  ```

**Business Logic**:

- **configs field semantic**: "When updating configs, all configs and values must be
  provided. Existing ones are matched, new ones are created, and configs not provided in
  the update are deleted."
- To remove all configs: Delete all variants first, then omit configs field from update
- Empty array would be ambiguous: "delete all" vs "no change intended"

**Questions for Katana Team**:

1. **Design Intent**: Is the "omit vs empty array" pattern intentional to prevent
   accidental deletion?

1. **Other Fields**: Are there other array fields in update operations that follow this
   pattern?

1. **Consistency**: Should all update operation array fields follow this pattern, or
   only some?

1. **Documentation**: Can this requirement be added to API documentation for affected
   endpoints?

**Recommendation**:

- **Document Pattern**: Clearly document which array fields reject empty arrays in
  update operations
- **Error Messages**: Provide clear validation error messages when empty arrays are sent
- **API Guidelines**: Establish consistent pattern for handling empty arrays across all
  update operations
- **Consider Alternative**: Add explicit "delete all" operations for fields where
  clearing is a valid use case

### Comprehensive Array Field Validation Analysis

**Issue**: Systematic review of all array field validation constraints across Create and
Update request schemas to ensure consistency and correctness.

**Analysis Date**: December 2024 **Total Create/Update Request Schemas Analyzed**: 58
**Total Array Fields Found**: 29

#### Summary of Findings

We conducted a comprehensive analysis of all array fields in Create and Update request
schemas to understand validation patterns and identify inconsistencies. Array fields
were categorized by two dimensions:

1. **Required vs Optional** (at schema level)
1. **With minItems vs Without minItems** constraint

This creates four distinct patterns, each with different semantics and use cases.

______________________________________________________________________

#### Category 1: ✅ Required Fields WITH minItems (Correct Pattern)

**Count**: 9 fields **Status**: ✅ **CORRECT** - This is the ideal pattern

These fields are REQUIRED at the schema level AND have minItems constraint. This is the
**correct pattern** because:

- The field MUST be sent (cannot be omitted)
- The field MUST contain at least one item
- Empty array would be logically invalid (entity doesn't make sense without items)

**Examples**:

- **CreateSalesOrderRequest.sales_order_rows** (minItems: 1) - Sales order without line
  items is meaningless
- **CreateSalesReturnRequest.sales_return_rows** (minItems: 1) - Return without items is
  meaningless
- **CreatePurchaseOrderRequest.purchase_order_rows** (minItems: 1) - Purchase order
  without line items is invalid
- **CreateMaterialRequest.variants** (minItems: 1) - Material must have at least one
  variant
- **CreateProductRequest.variants** (minItems: 1) - Product must have at least one
  variant
- **CreateWebhookRequest.subscribed_events** (minItems: 1) - Webhook without events is
  pointless
- **UpdateWebhookRequest.subscribed_events** (minItems: 1) - Webhook must always have
  events
- **CreateRecipesRequest.rows** (minItems: 1) - Recipe without rows is invalid
- **CreateServiceRequest.variants** (minItems: 1) - Service must have exactly one
  variant

**Pattern Characteristics**:

- Represents core business data essential to the entity
- Without these items, the entity has no purpose or meaning
- Enforces business rules at schema level

______________________________________________________________________

#### Category 2: ❌ Required Fields WITHOUT minItems (Inconsistency - NOW FIXED)

**Count**: 0 fields (2 fields WERE in this category, now fixed) **Status**: ✅ **FIXED**

- Added minItems: 1 to inconsistent fields

**Previously Inconsistent Fields (Now Fixed)**:

- ~~CreateSalesOrderRequest.sales_order_rows~~ → **FIXED**: Added minItems: 1
- ~~CreateSalesReturnRequest.sales_return_rows~~ → **FIXED**: Added minItems: 1

**Why This Was Inconsistent**:

- Field is REQUIRED (must be sent)
- But allowed empty array `[]`
- Logically invalid: Why require sending an empty array?
- Creates confusion: Is empty array valid or not?

**Our Fix**:

We added `minItems: 1` to both fields in our OpenAPI specification to align with the
correct pattern (Category 1).

______________________________________________________________________

#### Category 3: ⚠️ Optional Fields WITH minItems (Special "Omit vs Empty" Pattern)

**Count**: 4 fields **Status**: ⚠️ **INTENTIONAL PATTERN** - Implements "omit vs empty"
semantics

These fields are OPTIONAL at the schema level BUT have minItems constraint. This
implements the **"omit vs empty" pattern**:

**Semantics**:

- **Omitting field** = preserve existing values (no change)
- **Sending empty array `[]`** = REJECTED with 422 validation error
- **Sending non-empty array** = update/replace values

**Fields Using This Pattern**:

- **CreateProductRequest.configs** (minItems: 1) - Product configs for variant creation
- **UpdateProductRequest.configs** (minItems: 1) - Update product variant configs
- **UpdateMaterialRequest.configs** (minItems: 1) - Update material variant configs
- **CreateVariantRequest.config_attributes** (minItems: 1) - Variant configuration
  attributes

**Why This Pattern Exists**:

- Prevents accidental data deletion
- Makes developer intent explicit
- Clear distinction between "don't change" vs "set to empty"
- Documented in UpdateMaterialRequest.configs description:
  > "When updating configs, all configs and values must be provided. Existing ones are
  > matched, new ones are created, and configs not provided in the update are deleted."

**Client Impact**:

Developers must filter out empty arrays before sending:

```python
# Filter out empty configs - API rejects empty arrays
updates = {"name": "Product", "configs": []}
filtered = {k: v for k, v in updates.items()
            if not (k == "configs" and isinstance(v, list) and len(v) == 0)}
```

______________________________________________________________________

#### Category 4: ✅ Optional Fields WITHOUT minItems (Metadata Pattern)

**Count**: 16 fields **Status**: ✅ **CORRECT** - Appropriate for supplementary metadata

These fields are OPTIONAL and lack minItems constraint. This is **appropriate** for
supplementary metadata fields where empty arrays have clear semantics:

**Semantics**:

- **Empty array `[]`** = explicitly set to "no values" / clear all
- **Omitted field** = preserve existing values
- **Non-empty array** = set new values

**Fields Using This Pattern**:

**Manufacturing Data** (6 fields):

- CreateManufacturingOrderProductionRequest.ingredients
- CreateManufacturingOrderProductionRequest.operations
- UpdateManufacturingOrderProductionRequest.ingredients
- UpdateManufacturingOrderProductionRequest.operations
- CreateManufacturingOrderRecipeRowRequest.batch_transactions
- UpdateManufacturingOrderRecipeRowRequest.batch_transactions

**Variant Metadata** (6 fields):

- CreateVariantRequest.supplier_item_codes
- CreateVariantRequest.custom_fields
- UpdateVariantRequest.supplier_item_codes
- UpdateVariantRequest.config_attributes
- UpdateVariantRequest.custom_fields
- CreateServiceVariantRequest.custom_fields

**Other Optional Data** (4 fields):

- CreateMaterialRequest.configs
- CreateSalesOrderRequest.addresses
- CreateSupplierRequest.addresses
- UpdateManufacturingOrderOperationRowRequest.completed_by_operators

**Why This Pattern Is Correct**:

- These are supplementary fields, not core entity data
- Empty array has valid business meaning ("no additional data")
- Allows incremental data addition over time
- Provides flexibility for different workflows

______________________________________________________________________

#### Questions for Katana Development Team

1. **Pattern Standardization**: Should all required array fields have `minItems: 1`?

   - Our analysis shows this should be the standard pattern
   - We've aligned our spec to follow this pattern

1. **"Omit vs Empty" Pattern**: Is this pattern (Category 3) intentional for
   configuration fields?

   - If yes, should it extend to other similar fields?
   - Should documentation explicitly explain this pattern for all affected endpoints?

1. **Manufacturing Fields**: For optional manufacturing-related arrays (ingredients,
   operations, batch_transactions):

   - Is empty array `[]` a valid way to "clear all" values?
   - Or should these follow the "omit vs empty" pattern?

1. **API Documentation**: Can this validation behavior be documented per endpoint?

   - Which fields reject empty arrays
   - Which fields allow empty arrays
   - Clear examples showing the difference

1. **Validation Error Messages**: When empty arrays are rejected, can error messages
   explicitly state:

   - "Field X requires at least 1 item. To preserve existing values, omit this field
     entirely."

______________________________________________________________________

#### Recommendations for API Consistency

**For Katana API Team**:

1. **Standardize Required Arrays**: All required array fields should have `minItems: 1`
1. **Document Patterns**: Clearly document the three patterns (required, "omit vs
   empty", optional metadata)
1. **Error Messages**: Enhance validation errors to explain empty array rejection
1. **OpenAPI Spec**: Align official spec with these patterns consistently

**For Client Developers**:

- Our OpenAPI specification correctly implements all four patterns
- Generated clients will enforce proper validation
- Understanding these patterns helps avoid integration errors

______________________________________________________________________

## Comprehensive Request Property Constraint Analysis

**Analysis Date**: December 2024 **Analysis Scope**: All 85 request endpoints in the
OpenAPI specification **Total Properties Analyzed**: 491 **Automated Script**:
[extract_request_property_descriptions.py](../scripts/extract_request_property_descriptions.py)

### Executive Summary

We performed a comprehensive automated analysis of all request property descriptions
across the entire Katana API specification, looking for opportunities to add validation
constraints beyond array minItems. The analysis examined property descriptions for
keywords indicating potential constraints like string formats, number ranges, pattern
requirements, and required field semantics.

**Key Findings**:

- **Automated suggestions**: 34 properties flagged
- **False positives**: 25 properties (74%) - keyword matching errors
- **Valid opportunities**: 9 properties (26%)
  - Email format validation: 2 fields ✅ **HIGH PRIORITY**
  - Date-time format validation: 2 fields ✅ **HIGH PRIORITY**
  - URL format enhancement: 2 fields ⚠️ (optional)
  - Description vs schema inconsistencies: 3 fields ❓ **NEEDS CLARIFICATION**

### Actionable Constraint Opportunities

#### 1. Email Format Validation (HIGH PRIORITY)

**Fields Affected**:

- `POST /suppliers` → `CreateSupplierRequest.email`
- `PATCH /suppliers/{id}` → `UpdateSupplierRequest.email`

**Current State**:

```yaml
email:
  type: string
  description: Primary email address for supplier communication and order confirmations
```

**Recommendation**:

```yaml
email:
  type: string
  format: email  # ADD THIS
  description: Primary email address for supplier communication and order confirmations
```

**Rationale**: These fields explicitly store email addresses for business communication.
Standard email format validation should be enforced.

**Impact**: Prevents invalid email addresses from being stored, improving data quality
and reducing failed communications.

#### 2. Date-Time Format Validation (HIGH PRIORITY)

**Fields Affected**:

- `PATCH /purchase_orders/{id}` → `UpdatePurchaseOrderRequest.expected_arrival_date`
- `PATCH /purchase_order_rows/{id}` → `UpdatePurchaseOrderRowRequest.arrival_date`

**Current State**:

```yaml
# UpdatePurchaseOrderRequest
expected_arrival_date:
  type: string
  description: Updatable only when status is in NOT_RECEIVED or PARTIALLY_RECEIVED. Update will override arrival_date on purchase order rows

# UpdatePurchaseOrderRowRequest
arrival_date:
  type: string
  description: Updatable only when received_date is not null
```

**Recommendation**:

```yaml
# UpdatePurchaseOrderRequest
expected_arrival_date:
  type: string
  format: date-time  # ADD THIS
  description: Updatable only when status is in NOT_RECEIVED or PARTIALLY_RECEIVED. Update will override arrival_date on purchase order rows

# UpdatePurchaseOrderRowRequest
arrival_date:
  type: string
  format: date-time  # ADD THIS
  description: Updatable only when received_date is not null
```

**Rationale**: These fields store date-time values (examples in spec show ISO 8601
format like "2024-02-15T10:00:00Z"). The corresponding CREATE request schemas already
have `format: date-time` on these fields. The UPDATE schemas are missing this
constraint, creating inconsistency.

**Evidence**:

- CreatePurchaseOrderRowRequest.arrival_date: `format: date-time` ✅
- UpdatePurchaseOrderRowRequest.arrival_date: Missing format ❌
- Examples in spec show: `"arrival_date": "2024-02-15T10:00:00Z"`

**Impact**: Ensures date-time values are properly validated and formatted consistently
across CREATE and UPDATE operations.

#### 3. URL Format Enhancement (OPTIONAL)

**Fields Affected**:

- `POST /webhooks` → `CreateWebhookRequest.url`
- `PATCH /webhooks/{id}` → `UpdateWebhookRequest.url`

**Current State**:

```yaml
url:
  type: string
  pattern: ^https://.*$
  description: HTTPS endpoint URL where webhook events will be sent (must use HTTPS for security)
```

**Optional Enhancement**:

```yaml
url:
  type: string
  format: uri  # ADD THIS for semantic clarity
  pattern: ^https://.*$
  description: HTTPS endpoint URL where webhook events will be sent (must use HTTPS for security)
```

**Rationale**: The pattern constraint already enforces HTTPS requirement. Adding
`format: uri` provides semantic clarity but is not strictly necessary since the pattern
is sufficient.

**Priority**: Low - Current validation is adequate

### Description vs Schema Inconsistencies (NEEDS CLARIFICATION)

The following fields have descriptions containing the word "required" but are marked as
optional in the schema. This needs Katana team review to clarify intended semantics.

#### BOM Row Quantity Fields

**POST /bom_rows** → `CreateBomRowRequest.quantity`:

- **Schema**: `type: ['number', 'null']`, `required: false`
- **Description**: "**Required** quantity of the ingredient variant"
- **Current constraints**: `minimum: 0`, `maximum: 100000000000000000`

**PATCH /bom_rows/{id}** → `UpdateBomRowRequest.quantity`:

- **Schema**: `type: ['number', 'null']`, `required: false`
- **Description**: "**Required** quantity of the ingredient variant"
- **Current constraints**: `minimum: 0`, `maximum: 100000000000000000`

**Question for Katana Team**: Is `quantity` semantically required for BOM rows, or is
`null`/omitted valid? If required, should schema be `required: true`?

#### Outsourced Purchase Order Recipe Row Quantity

**POST /outsourced_purchase_order_recipe_rows** → `quantity`:

- **Schema**: `type: number`, `required: true` ✅
- **Description**: "Quantity **required**"
- **Current constraints**: `minimum: 0`

**PATCH /outsourced_purchase_order_recipe_rows/{id}** → `quantity`:

- **Schema**: `type: number`, `required: false` ❌
- **Description**: "Quantity **required**"
- **Current constraints**: `minimum: 0`

**Inconsistency**: POST marks quantity as required, but PATCH marks it optional despite
identical "required" description.

**Question for Katana Team**: Should PATCH also mark quantity as `required: true` to
match POST endpoint?

### False Positives (Analysis Artifacts)

The automated analysis flagged 27 properties that appear to need constraints but are
actually correct as-is. These are documented here to prevent future confusion:

#### Incorrect String Format Suggestions

| Field                       | Wrong Suggestion                | Why It's Wrong                                          |
| --------------------------- | ------------------------------- | ------------------------------------------------------- |
| `batch_number`              | `format: date`                  | Batch number is an identifier string, not a date value  |
| `name` (products/materials) | `format: uri`                   | Names are human-readable display strings, not URIs      |
| `additional_info`           | `format: uri` or `format: date` | Free-text field for notes/comments, not structured data |
| `purchase_uom`              | `format: date`                  | Unit of measure abbreviation (max 7 chars), not a date  |

**Root Cause**: Keyword matching in descriptions (e.g., "inventory and manufacturing"
contains "uri", "batch" contains "date").

#### Already Adequately Constrained Fields

| Field                                     | Suggestion             | Why Not Needed                                                          |
| ----------------------------------------- | ---------------------- | ----------------------------------------------------------------------- |
| `received_date`, `start_date`, `end_date` | Add pattern constraint | Already have `format: date-time` which enforces ISO 8601                |
| `currency` fields                         | Add pattern constraint | ISO 4217 documented in description; pattern would be overly restrictive |
| `format` (webhook_logs_export)            | Add pattern constraint | Already has `enum: ['csv', 'json']` - exhaustive validation             |

#### Correctly Optional Fields with "Required" Context

These fields mention "required" in their descriptions but are correctly optional in the
schema:

- **UpdateMaterialRequest.configs**: Description says "all configs and values **must**
  be provided" - This means IF you provide the configs array, it must be complete. The
  field itself is correctly optional (omit vs empty pattern).

- **UpdateProductRequest.configs**: Same as above - implements "omit vs empty" pattern
  documented in our comprehensive array validation analysis.

- **CreateVariantRequest.lead_time**: Description says "Days **required** to
  manufacture" - This describes what the value represents (required lead time), not that
  the field itself is required.

- **WebhookRequest.subscribed_events**: Already correctly marked as `required: true`
  with `minItems: 1`. Description reinforces the schema; no change needed.

### Analysis Methodology

#### Script Implementation

Created automated analysis script
([extract_request_property_descriptions.py](../scripts/extract_request_property_descriptions.py))
that:

1. Parses the OpenAPI YAML specification
1. Extracts all request body schemas across 85 endpoints
1. Recursively resolves `$ref`, `allOf`, `oneOf`, `anyOf` schema compositions
1. Analyzes property descriptions for constraint keywords:
   - **String constraints**: "email", "url", "uuid", "date", "pattern", "format"
   - **Number constraints**: "minimum", "maximum", "at least", "at most", "between",
     "positive"
   - **Array constraints**: "at least one", "cannot be empty", "must contain"
   - **Required semantics**: "required", "must be provided", "mandatory"
1. Compares detected patterns against existing constraints
1. Generates suggestions for missing constraints

#### Outputs Generated

1. **constraint_analysis_report.md** - Full automated report with all 34 flagged
   properties
1. **constraint_analysis.csv** - Spreadsheet format for easier filtering and analysis
1. **constraint_opportunities_refined.md** - Manual review filtering false positives to
   7 actionable items

#### Limitations of Automated Analysis

- **Keyword matching** generates many false positives (79% in this case)
- **Context understanding** requires human review (e.g., "required" can mean different
  things)
- **Business logic** cannot be inferred from descriptions alone
- **Existing patterns** (like "omit vs empty") require domain knowledge to recognize

**Conclusion**: Automated analysis is valuable for **discovery** but requires **manual
review** to separate signal from noise.

### Questions for Katana Development Team

1. **Email Validation**: Should we add `format: email` to supplier email fields?
   (Recommended: Yes)

1. **Date-Time Validation**: Should we add `format: date-time` to
   UpdatePurchaseOrderRequest.expected_arrival_date and
   UpdatePurchaseOrderRowRequest.arrival_date for consistency with CREATE schemas?
   (Recommended: Yes)

1. **BOM Row Quantities**: Are BOM row quantities semantically required, or is
   `null`/omitted valid? If required, should schema reflect this?

1. **Outsourced PO Recipe Rows**: Should PATCH endpoint require `quantity` field to
   match POST endpoint behavior?

1. **Required Field Semantics**: When descriptions say "required," does this mean:

   - Required in schema (must be provided in request)?
   - Semantically required (has business meaning/purpose)?
   - Conditionally required (depends on other fields/state)?

1. **Nullable vs Optional Pattern**: Fields with `type: ['number', 'null']` +
   `required: false` create ambiguity:

   - Should these be `required: true, type: ['number', 'null']` (must provide field, can
     be null)?
   - Or `required: false, type: number` (can omit field entirely)?
   - What's the semantic difference between omitted vs null?

1. **Future Constraint Enhancements**: Are there other validation rules not captured in
   the OpenAPI spec that should be documented? (e.g., business rules, conditional
   validations, field interdependencies)

### Recommendations for Specification Maintenance

1. **Standardize Email Fields**: All fields storing email addresses should use
   `format: email` for consistency

1. **Clarify "Required" Usage**: Distinguish in descriptions between:

   - Schema-required (must be in request)
   - Semantically required (business meaning)
   - Conditionally required (depends on context)

1. **Document Nullable Semantics**: For fields that accept null, document what null
   means vs omitting the field

1. **Pattern Documentation**: When using custom patterns (like webhook HTTPS), document
   the rationale in field descriptions

1. **Automated Spec Linting**: Consider implementing spec linting rules:

   - All email fields should have `format: email`
   - Description "required" should match `required: true` in schema
   - Fields with validation rules should document them consistently

### Related Analysis

This analysis builds on our previous
[Comprehensive Array Field Validation Analysis](#comprehensive-array-field-validation-analysis)
which identified and fixed missing `minItems` constraints. Together, these analyses
provide complete coverage of validation constraint opportunities across the entire API
specification.

**Previous Fixes**:

- Added `minItems: 1` to CreateSalesOrderRequest.sales_order_rows
- Added `minItems: 1` to CreateSalesReturnRequest.sales_return_rows
- Documented "omit vs empty" validation pattern for optional arrays

**Current Findings**:

- 2 email fields need `format: email` (HIGH PRIORITY) → IMPLEMENTED
- 2 date-time fields need `format: date-time` (HIGH PRIORITY) → IMPLEMENTED
- 3 quantity fields have description/schema inconsistencies (NEEDS CLARIFICATION)
- 25 false positives documented to prevent future confusion

______________________________________________________________________

## Deep Constraint Analysis - ISO Standards Implementation

**Analysis Date**: December 2024 **Scope**: Comprehensive analysis of all request
properties for ISO standard enforcement

### Constraints Implemented

We performed a deep analysis of the OpenAPI spec looking for fields that explicitly
mention ISO standards in their descriptions. Based on this analysis, we implemented the
following constraints:

#### Email Format Validation (4 fields implemented)

**Fields**:

- `CreateCustomerRequest.email` → `format: email`
- `UpdateCustomerRequest.email` → `format: email`
- `CreateSupplierRequest.email` → `format: email`
- `UpdateSupplierRequest.email` → `format: email`

**Rationale**: All email fields should use standard email format validation for data
quality.

#### Date-Time Format Validation (6 additional fields implemented)

**Fields**:

- `CreateSalesOrderRequest.tracking_number_url` → `format: uri`
- `UpdatePurchaseOrderRequest.expected_arrival_date` → `format: date-time`
- `UpdatePurchaseOrderRowRequest.arrival_date` → `format: date-time`
- `UpdatePurchaseOrderRowRequest.received_date` → `format: date-time`
- `CreateSalesOrderRequest.order_created_date` → `format: date-time`
- `CreateSalesOrderRequest.delivery_date` → `format: date-time`

**Rationale**: Consistency with other date-time fields. Examples in spec show ISO 8601
format.

#### ISO 4217 Currency Pattern (10 fields implemented)

**Fields**:

- `CreatePurchaseOrderRequest.currency` → `pattern: ^[A-Z]{3}$`
- `CreateSupplierRequest.currency` → `pattern: ^[A-Z]{3}$`
- `UpdateSupplierRequest.currency` → `pattern: ^[A-Z]{3}$`
- `CreatePriceListRequest.currency` → `pattern: ^[A-Z]{3}$`
- `UpdatePriceListRequest.currency` → `pattern: ^[A-Z]{3}$`
- `CreatePriceListRowRequest.currency` → `pattern: ^[A-Z]{3}$`
- `UpdatePriceListRowRequest.currency` → `pattern: ^[A-Z]{3}$`
- `CreateSalesOrderRequest.currency` → `pattern: ^[A-Z]{3}$`
- `CreateSalesReturnRequest.currency` → `pattern: ^[A-Z]{3}$`
- `Factory.default_currency` → `pattern: ^[A-Z]{3}$`

**Rationale**: All these fields explicitly state "ISO 4217" in their descriptions. All
examples in the spec use 3-letter uppercase codes (USD, EUR, GBP). Pattern enforces the
standard format.

**Example**:

```yaml
currency:
  type: string
  pattern: ^[A-Z]{3}$
  description: Active ISO 4217 currency code (e.g. USD, EUR).
```

#### Example Value Corrections

Fixed inconsistent country code examples to match ISO 3166-1 alpha-2 format mentioned in
descriptions:

- Changed `country: USA` → `country: US` (5 occurrences)
- Changed `country: United States` → `country: US` (1 occurrence)

### Questions for Katana Development Team

#### Country Code Validation - NEEDS CLARIFICATION

**Issue**: Multiple country code fields mention "ISO 3166-1 alpha-2 format" in
descriptions, but we have concerns about enforcing this with pattern constraints.

**Fields in question** (6 total):

- `SupplierAddressRequest.country` - "Country code (ISO 3166-1 alpha-2 format)"
- `CreateSupplierAddressRequest.country` - "Country code (ISO 3166-1 alpha-2 format)"
- `UpdateSupplierAddressRequest.country` - "Country code (ISO 3166-1 alpha-2 format)"
- `CreateSalesOrderAddressRequest.country` - "Country code"
- `UpdateSalesOrderAddressRequest.country` - "Country code"
- `CreateCustomerAddressRequest.country` - "Country name or country code"

**Examples were inconsistent**:

- Some showed `USA` (3-letter, ISO 3166-1 alpha-3)
- Some showed `US` (2-letter, ISO 3166-1 alpha-2)
- One showed `United States` (full name)

**We corrected all examples to `US` but did NOT add pattern constraints.**

**Questions**:

1. **Should country code fields enforce ISO 3166-1 alpha-2?**

   - If YES: Add `pattern: ^[A-Z]{2}$` to supplier/sales order address country fields
   - If NO: Update descriptions to clarify that multiple formats are accepted

1. **Address data flexibility**: Should address fields (supplier addresses, customer
   addresses, sales order addresses) accept flexible country formats since this data
   often comes from external systems?

1. **Recommendation**: We suggest NOT enforcing strict patterns on address country
   fields to allow flexibility for international address data, but would like Katana
   team's guidance on the intended behavior.

**Current State**:

- ✅ Examples corrected to ISO 3166-1 alpha-2 format
- ❌ NO pattern constraints added (awaiting clarification)
- ⚠️ Descriptions still mention "ISO 3166-1 alpha-2 format"

**Potential Pattern** (if approved):

```yaml
country:
  type: string
  pattern: ^[A-Z]{2}$
  description: Country code (ISO 3166-1 alpha-2 format)
```

#### Other ISO Standard Questions

4. **Currency code flexibility**: We added `pattern: ^[A-Z]{3}$` to all fields
   explicitly mentioning ISO 4217. Should test environments be able to use fake currency
   codes like "XXX" or "TST"?

1. **Date-time format consistency**: Should ALL date-related fields use
   `format: date-time` even if they only conceptually represent dates (like
   `delivery_date`), or should some use `format: date`?

### Summary Statistics

**Total constraints added in this session**: 20

- Email format: 4 fields
- URI format: 1 field
- Date-time format: 5 fields
- ISO 4217 currency pattern: 10 fields

**Example corrections**: 6 country code values normalized to ISO 3166-1 alpha-2

**Pending clarification**: Country code pattern enforcement (6 fields)
