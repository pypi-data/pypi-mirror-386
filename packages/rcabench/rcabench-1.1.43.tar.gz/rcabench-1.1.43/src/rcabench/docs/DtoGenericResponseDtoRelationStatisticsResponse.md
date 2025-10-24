# DtoGenericResponseDtoRelationStatisticsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | Status code | [optional] 
**data** | [**DtoRelationStatisticsResponse**](DtoRelationStatisticsResponse.md) |  | [optional] 
**message** | **str** | Response message | [optional] 
**timestamp** | **int** | Response generation time | [optional] 

## Example

```python
from rcabench.openapi.models.dto_generic_response_dto_relation_statistics_response import DtoGenericResponseDtoRelationStatisticsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DtoGenericResponseDtoRelationStatisticsResponse from a JSON string
dto_generic_response_dto_relation_statistics_response_instance = DtoGenericResponseDtoRelationStatisticsResponse.from_json(json)
# print the JSON string representation of the object
print DtoGenericResponseDtoRelationStatisticsResponse.to_json()

# convert the object into a dict
dto_generic_response_dto_relation_statistics_response_dict = dto_generic_response_dto_relation_statistics_response_instance.to_dict()
# create an instance of DtoGenericResponseDtoRelationStatisticsResponse from a dict
dto_generic_response_dto_relation_statistics_response_form_dict = dto_generic_response_dto_relation_statistics_response.from_dict(dto_generic_response_dto_relation_statistics_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


