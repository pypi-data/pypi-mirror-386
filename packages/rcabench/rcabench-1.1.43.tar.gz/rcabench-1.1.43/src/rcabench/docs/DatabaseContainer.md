# DatabaseContainer


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**command** | **str** | Startup command | [optional] 
**created_at** | **str** | Creation time | [optional] 
**env_vars** | **str** | List of environment variable names | [optional] 
**helm_config** | [**DatabaseHelmConfig**](DatabaseHelmConfig.md) |  | [optional] 
**helm_config_id** | **int** | Associated Helm configuration, nullable | [optional] 
**id** | **int** | Unique identifier | [optional] 
**image** | **str** | Full image name (not stored in DB, used for display) | [optional] 
**is_public** | **bool** | Whether publicly visible | [optional] 
**name** | **str** | Name with size limit | [optional] 
**registry** | **str** | Image registry with size limit | [optional] 
**repository** | **str** | Image repository with size limit | [optional] 
**status** | **int** | Status: -1:deleted 0:disabled 1:active | [optional] 
**tag** | **str** | Image tag with size limit | [optional] 
**type** | **str** | Image type | [optional] 
**updated_at** | **str** | Update time | [optional] 
**user** | [**DatabaseUser**](DatabaseUser.md) |  | [optional] 
**user_id** | **int** | Container must belong to a user | [optional] 

## Example

```python
from rcabench.openapi.models.database_container import DatabaseContainer

# TODO update the JSON string below
json = "{}"
# create an instance of DatabaseContainer from a JSON string
database_container_instance = DatabaseContainer.from_json(json)
# print the JSON string representation of the object
print DatabaseContainer.to_json()

# convert the object into a dict
database_container_dict = database_container_instance.to_dict()
# create an instance of DatabaseContainer from a dict
database_container_form_dict = database_container.from_dict(database_container_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


