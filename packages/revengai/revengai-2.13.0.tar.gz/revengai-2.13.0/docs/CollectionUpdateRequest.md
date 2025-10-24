# CollectionUpdateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**collection_scope** | [**CollectionScope**](CollectionScope.md) |  | [optional] 

## Example

```python
from revengai.models.collection_update_request import CollectionUpdateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionUpdateRequest from a JSON string
collection_update_request_instance = CollectionUpdateRequest.from_json(json)
# print the JSON string representation of the object
print(CollectionUpdateRequest.to_json())

# convert the object into a dict
collection_update_request_dict = collection_update_request_instance.to_dict()
# create an instance of CollectionUpdateRequest from a dict
collection_update_request_from_dict = CollectionUpdateRequest.from_dict(collection_update_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


