# BaseResponseAnalysisFunctionMapping


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**AnalysisFunctionMapping**](AnalysisFunctionMapping.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_analysis_function_mapping import BaseResponseAnalysisFunctionMapping

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseAnalysisFunctionMapping from a JSON string
base_response_analysis_function_mapping_instance = BaseResponseAnalysisFunctionMapping.from_json(json)
# print the JSON string representation of the object
print(BaseResponseAnalysisFunctionMapping.to_json())

# convert the object into a dict
base_response_analysis_function_mapping_dict = base_response_analysis_function_mapping_instance.to_dict()
# create an instance of BaseResponseAnalysisFunctionMapping from a dict
base_response_analysis_function_mapping_from_dict = BaseResponseAnalysisFunctionMapping.from_dict(base_response_analysis_function_mapping_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


