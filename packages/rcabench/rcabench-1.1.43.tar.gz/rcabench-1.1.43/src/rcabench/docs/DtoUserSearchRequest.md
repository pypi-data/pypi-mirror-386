# DtoUserSearchRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_at** | [**DtoDateRange**](DtoDateRange.md) |  | [optional] 
**departments** | **List[str]** | Department filter | [optional] 
**email_pattern** | **str** | Email fuzzy match | [optional] 
**exclude_fields** | **List[str]** |  | [optional] 
**filters** | [**List[DtoSearchFilter]**](DtoSearchFilter.md) | Filters | [optional] 
**fullname_pattern** | **str** | Full name fuzzy match | [optional] 
**include** | **List[str]** | Include related entities | [optional] 
**include_fields** | **List[str]** | Include/Exclude fields | [optional] 
**is_active** | **bool** |  | [optional] 
**keyword** | **str** | Search keyword (for general text search) | [optional] 
**last_login_range** | [**DtoDateRange**](DtoDateRange.md) |  | [optional] 
**page** | **int** | Pagination | [optional] 
**project_id** | **int** |  | [optional] 
**project_ids** | **List[int]** | Project ID filter | [optional] 
**role_ids** | **List[int]** | Role ID filter | [optional] 
**size** | **int** |  | [optional] 
**sort** | [**List[DtoSortOption]**](DtoSortOption.md) | Sort | [optional] 
**status** | **List[int]** |  | [optional] 
**updated_at** | [**DtoDateRange**](DtoDateRange.md) |  | [optional] 
**user_id** | **int** |  | [optional] 
**username_pattern** | **str** | User-specific filter shortcuts | [optional] 

## Example

```python
from rcabench.openapi.models.dto_user_search_request import DtoUserSearchRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DtoUserSearchRequest from a JSON string
dto_user_search_request_instance = DtoUserSearchRequest.from_json(json)
# print the JSON string representation of the object
print DtoUserSearchRequest.to_json()

# convert the object into a dict
dto_user_search_request_dict = dto_user_search_request_instance.to_dict()
# create an instance of DtoUserSearchRequest from a dict
dto_user_search_request_form_dict = dto_user_search_request.from_dict(dto_user_search_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


