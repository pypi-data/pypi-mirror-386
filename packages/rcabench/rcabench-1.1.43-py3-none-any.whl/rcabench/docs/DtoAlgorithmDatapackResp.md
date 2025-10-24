# DtoAlgorithmDatapackResp


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**algorithm** | **str** | Algorithm name | [optional] 
**datapack** | **str** | Datapack name | [optional] 
**executed_at** | **str** | Execution time | [optional] 
**execution_duration** | **float** | Execution duration in seconds | [optional] 
**execution_id** | **int** | Execution ID (0 if no execution found) | [optional] 
**found** | **bool** | Whether execution result was found | [optional] 
**groundtruth** | [**HandlerGroundtruth**](HandlerGroundtruth.md) |  | [optional] 
**predictions** | [**List[DtoGranularityRecord]**](DtoGranularityRecord.md) | Algorithm predictions | [optional] 

## Example

```python
from rcabench.openapi.models.dto_algorithm_datapack_resp import DtoAlgorithmDatapackResp

# TODO update the JSON string below
json = "{}"
# create an instance of DtoAlgorithmDatapackResp from a JSON string
dto_algorithm_datapack_resp_instance = DtoAlgorithmDatapackResp.from_json(json)
# print the JSON string representation of the object
print DtoAlgorithmDatapackResp.to_json()

# convert the object into a dict
dto_algorithm_datapack_resp_dict = dto_algorithm_datapack_resp_instance.to_dict()
# create an instance of DtoAlgorithmDatapackResp from a dict
dto_algorithm_datapack_resp_form_dict = dto_algorithm_datapack_resp.from_dict(dto_algorithm_datapack_resp_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


