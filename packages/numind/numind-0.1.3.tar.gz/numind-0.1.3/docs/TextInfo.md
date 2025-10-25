# TextInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**document_id** | **str** | Unique document identifier. | 
**file_id** | **str** | Unique file identifier of the file used to generate this document. | 
**file_name** | **str** | Filename of the initial file if any.     **None** for text input. | [optional] 
**text** | **str** | The text content of the document. | 
**possible_transformations** | **List[str]** | Possible transformations that can be done with this document. | [optional] 
**type** | **str** |  | 

## Example

```python
from numind.models.text_info import TextInfo

# TODO update the JSON string below
json = "{}"
# create an instance of TextInfo from a JSON string
text_info_instance = TextInfo.from_json(json)
# print the JSON string representation of the object
print(TextInfo.to_json())

# convert the object into a dict
text_info_dict = text_info_instance.to_dict()
# create an instance of TextInfo from a dict
text_info_from_dict = TextInfo.from_dict(text_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


