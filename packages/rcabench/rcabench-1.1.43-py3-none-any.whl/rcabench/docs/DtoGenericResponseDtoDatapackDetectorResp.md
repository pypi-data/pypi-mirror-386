# DtoGenericResponseDtoDatapackDetectorResp


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | Status code | [optional] 
**data** | [**DtoDatapackDetectorResp**](DtoDatapackDetectorResp.md) |  | [optional] 
**message** | **str** | Response message | [optional] 
**timestamp** | **int** | Response generation time | [optional] 

## Example

```python
from rcabench.openapi.models.dto_generic_response_dto_datapack_detector_resp import DtoGenericResponseDtoDatapackDetectorResp

# TODO update the JSON string below
json = "{}"
# create an instance of DtoGenericResponseDtoDatapackDetectorResp from a JSON string
dto_generic_response_dto_datapack_detector_resp_instance = DtoGenericResponseDtoDatapackDetectorResp.from_json(json)
# print the JSON string representation of the object
print DtoGenericResponseDtoDatapackDetectorResp.to_json()

# convert the object into a dict
dto_generic_response_dto_datapack_detector_resp_dict = dto_generic_response_dto_datapack_detector_resp_instance.to_dict()
# create an instance of DtoGenericResponseDtoDatapackDetectorResp from a dict
dto_generic_response_dto_datapack_detector_resp_form_dict = dto_generic_response_dto_datapack_detector_resp.from_dict(dto_generic_response_dto_datapack_detector_resp_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


