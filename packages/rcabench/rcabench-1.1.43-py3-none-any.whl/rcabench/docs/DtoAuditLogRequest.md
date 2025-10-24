# DtoAuditLogRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**action** | **str** |  | 
**details** | **str** |  | [optional] 
**resource** | **str** |  | 
**resource_id** | **int** |  | [optional] 

## Example

```python
from rcabench.openapi.models.dto_audit_log_request import DtoAuditLogRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DtoAuditLogRequest from a JSON string
dto_audit_log_request_instance = DtoAuditLogRequest.from_json(json)
# print the JSON string representation of the object
print DtoAuditLogRequest.to_json()

# convert the object into a dict
dto_audit_log_request_dict = dto_audit_log_request_instance.to_dict()
# create an instance of DtoAuditLogRequest from a dict
dto_audit_log_request_form_dict = dto_audit_log_request.from_dict(dto_audit_log_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


