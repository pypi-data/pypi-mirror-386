# ApiKeyResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**organization** | **str** |  | [optional] 
**name** | **str** |  | 
**token** | **str** |  | 
**user_id** | **str** |  | 
**created_at** | **str** |  | 
**expires_at** | **str** |  | 

## Example

```python
from numind.models.api_key_response import ApiKeyResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ApiKeyResponse from a JSON string
api_key_response_instance = ApiKeyResponse.from_json(json)
# print the JSON string representation of the object
print(ApiKeyResponse.to_json())

# convert the object into a dict
api_key_response_dict = api_key_response_instance.to_dict()
# create an instance of ApiKeyResponse from a dict
api_key_response_from_dict = ApiKeyResponse.from_dict(api_key_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


