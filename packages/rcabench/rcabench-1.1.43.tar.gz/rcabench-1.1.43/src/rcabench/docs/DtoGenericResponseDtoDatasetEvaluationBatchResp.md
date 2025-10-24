# DtoGenericResponseDtoDatasetEvaluationBatchResp


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | Status code | [optional] 
**data** | [**List[DtoAlgorithmDatasetResp]**](DtoAlgorithmDatasetResp.md) | Generic type data | [optional] 
**message** | **str** | Response message | [optional] 
**timestamp** | **int** | Response generation time | [optional] 

## Example

```python
from rcabench.openapi.models.dto_generic_response_dto_dataset_evaluation_batch_resp import DtoGenericResponseDtoDatasetEvaluationBatchResp

# TODO update the JSON string below
json = "{}"
# create an instance of DtoGenericResponseDtoDatasetEvaluationBatchResp from a JSON string
dto_generic_response_dto_dataset_evaluation_batch_resp_instance = DtoGenericResponseDtoDatasetEvaluationBatchResp.from_json(json)
# print the JSON string representation of the object
print DtoGenericResponseDtoDatasetEvaluationBatchResp.to_json()

# convert the object into a dict
dto_generic_response_dto_dataset_evaluation_batch_resp_dict = dto_generic_response_dto_dataset_evaluation_batch_resp_instance.to_dict()
# create an instance of DtoGenericResponseDtoDatasetEvaluationBatchResp from a dict
dto_generic_response_dto_dataset_evaluation_batch_resp_form_dict = dto_generic_response_dto_dataset_evaluation_batch_resp.from_dict(dto_generic_response_dto_dataset_evaluation_batch_resp_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


