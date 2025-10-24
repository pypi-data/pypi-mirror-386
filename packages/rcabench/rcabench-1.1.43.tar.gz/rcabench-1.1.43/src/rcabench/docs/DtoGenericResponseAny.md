# DtoGenericResponseAny


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | Status code | [optional] 
**data** | **object** | Generic type data | [optional] 
**message** | **str** | Response message | [optional] 
**timestamp** | **int** | Response generation time | [optional] 

## Example

```python
from rcabench.openapi.models.dto_generic_response_any import DtoGenericResponseAny

# TODO update the JSON string below
json = "{}"
# create an instance of DtoGenericResponseAny from a JSON string
dto_generic_response_any_instance = DtoGenericResponseAny.from_json(json)
# print the JSON string representation of the object
print DtoGenericResponseAny.to_json()

# convert the object into a dict
dto_generic_response_any_dict = dto_generic_response_any_instance.to_dict()
# create an instance of DtoGenericResponseAny from a dict
dto_generic_response_any_form_dict = dto_generic_response_any.from_dict(dto_generic_response_any_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


