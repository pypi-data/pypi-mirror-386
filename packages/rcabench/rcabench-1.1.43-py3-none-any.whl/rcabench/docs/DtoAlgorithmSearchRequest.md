# DtoAlgorithmSearchRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_at** | [**DtoDateRange**](DtoDateRange.md) |  | [optional] 
**exclude_fields** | **List[str]** |  | [optional] 
**filters** | [**List[DtoSearchFilter]**](DtoSearchFilter.md) | Filters | [optional] 
**image** | **str** |  | [optional] 
**include** | **List[str]** | Include related entities | [optional] 
**include_fields** | **List[str]** | Include/Exclude fields | [optional] 
**is_active** | **bool** |  | [optional] 
**keyword** | **str** | Search keyword (for general text search) | [optional] 
**name** | **str** | Algorithm-specific filters | [optional] 
**page** | **int** | Pagination | [optional] 
**project_id** | **int** |  | [optional] 
**size** | **int** |  | [optional] 
**sort** | [**List[DtoSortOption]**](DtoSortOption.md) | Sort | [optional] 
**status** | **List[int]** |  | [optional] 
**tag** | **str** |  | [optional] 
**type** | **str** |  | [optional] 
**updated_at** | [**DtoDateRange**](DtoDateRange.md) |  | [optional] 
**user_id** | **int** |  | [optional] 

## Example

```python
from rcabench.openapi.models.dto_algorithm_search_request import DtoAlgorithmSearchRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DtoAlgorithmSearchRequest from a JSON string
dto_algorithm_search_request_instance = DtoAlgorithmSearchRequest.from_json(json)
# print the JSON string representation of the object
print DtoAlgorithmSearchRequest.to_json()

# convert the object into a dict
dto_algorithm_search_request_dict = dto_algorithm_search_request_instance.to_dict()
# create an instance of DtoAlgorithmSearchRequest from a dict
dto_algorithm_search_request_form_dict = dto_algorithm_search_request.from_dict(dto_algorithm_search_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


