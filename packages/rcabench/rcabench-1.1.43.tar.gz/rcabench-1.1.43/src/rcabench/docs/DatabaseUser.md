# DatabaseUser


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**avatar** | **str** | Avatar URL with size limit | [optional] 
**created_at** | **str** | Creation time | [optional] 
**email** | **str** | Email (unique) with size limit | [optional] 
**full_name** | **str** | Full name with size limit | [optional] 
**id** | **int** | Unique identifier | [optional] 
**is_active** | **bool** | Whether active | [optional] 
**last_login_at** | **str** | Last login time | [optional] 
**phone** | **str** | Phone number | [optional] 
**status** | **int** | Status: -1:deleted 0:disabled 1:enabled | [optional] 
**updated_at** | **str** | Update time | [optional] 
**username** | **str** | Username (unique) with size limit | [optional] 

## Example

```python
from rcabench.openapi.models.database_user import DatabaseUser

# TODO update the JSON string below
json = "{}"
# create an instance of DatabaseUser from a JSON string
database_user_instance = DatabaseUser.from_json(json)
# print the JSON string representation of the object
print DatabaseUser.to_json()

# convert the object into a dict
database_user_dict = database_user_instance.to_dict()
# create an instance of DatabaseUser from a dict
database_user_form_dict = database_user.from_dict(database_user_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


