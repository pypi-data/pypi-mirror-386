# BaseResponseTagSearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**TagSearchResponse**](TagSearchResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_tag_search_response import BaseResponseTagSearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseTagSearchResponse from a JSON string
base_response_tag_search_response_instance = BaseResponseTagSearchResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseTagSearchResponse.to_json())

# convert the object into a dict
base_response_tag_search_response_dict = base_response_tag_search_response_instance.to_dict()
# create an instance of BaseResponseTagSearchResponse from a dict
base_response_tag_search_response_from_dict = BaseResponseTagSearchResponse.from_dict(base_response_tag_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


