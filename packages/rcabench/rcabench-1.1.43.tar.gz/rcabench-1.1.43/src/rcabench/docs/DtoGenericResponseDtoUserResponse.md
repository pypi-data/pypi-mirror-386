# DtoGenericResponseDtoUserResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | Status code | [optional] 
**data** | [**DtoUserResponse**](DtoUserResponse.md) |  | [optional] 
**message** | **str** | Response message | [optional] 
**timestamp** | **int** | Response generation time | [optional] 

## Example

```python
from rcabench.openapi.models.dto_generic_response_dto_user_response import DtoGenericResponseDtoUserResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DtoGenericResponseDtoUserResponse from a JSON string
dto_generic_response_dto_user_response_instance = DtoGenericResponseDtoUserResponse.from_json(json)
# print the JSON string representation of the object
print DtoGenericResponseDtoUserResponse.to_json()

# convert the object into a dict
dto_generic_response_dto_user_response_dict = dto_generic_response_dto_user_response_instance.to_dict()
# create an instance of DtoGenericResponseDtoUserResponse from a dict
dto_generic_response_dto_user_response_form_dict = dto_generic_response_dto_user_response.from_dict(dto_generic_response_dto_user_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


