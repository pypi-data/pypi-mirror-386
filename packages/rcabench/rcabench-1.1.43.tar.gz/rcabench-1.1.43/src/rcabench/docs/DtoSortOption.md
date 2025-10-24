# DtoSortOption


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**direction** | [**DtoSortDirection**](DtoSortDirection.md) |  | 
**field** | **str** | Sort field | 

## Example

```python
from rcabench.openapi.models.dto_sort_option import DtoSortOption

# TODO update the JSON string below
json = "{}"
# create an instance of DtoSortOption from a JSON string
dto_sort_option_instance = DtoSortOption.from_json(json)
# print the JSON string representation of the object
print DtoSortOption.to_json()

# convert the object into a dict
dto_sort_option_dict = dto_sort_option_instance.to_dict()
# create an instance of DtoSortOption from a dict
dto_sort_option_form_dict = dto_sort_option.from_dict(dto_sort_option_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


