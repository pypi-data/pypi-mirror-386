# DtoGenericResponseDtoInjectCancelResp


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | Status code | [optional] 
**data** | **object** |  | [optional] 
**message** | **str** | Response message | [optional] 
**timestamp** | **int** | Response generation time | [optional] 

## Example

```python
from rcabench.openapi.models.dto_generic_response_dto_inject_cancel_resp import DtoGenericResponseDtoInjectCancelResp

# TODO update the JSON string below
json = "{}"
# create an instance of DtoGenericResponseDtoInjectCancelResp from a JSON string
dto_generic_response_dto_inject_cancel_resp_instance = DtoGenericResponseDtoInjectCancelResp.from_json(json)
# print the JSON string representation of the object
print DtoGenericResponseDtoInjectCancelResp.to_json()

# convert the object into a dict
dto_generic_response_dto_inject_cancel_resp_dict = dto_generic_response_dto_inject_cancel_resp_instance.to_dict()
# create an instance of DtoGenericResponseDtoInjectCancelResp from a dict
dto_generic_response_dto_inject_cancel_resp_form_dict = dto_generic_response_dto_inject_cancel_resp.from_dict(dto_generic_response_dto_inject_cancel_resp_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


