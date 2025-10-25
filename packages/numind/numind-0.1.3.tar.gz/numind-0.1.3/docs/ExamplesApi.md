# numind.openapi_client.ExamplesApi

All URIs are relative to *https://nuextract.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_api_projects_projectid_examples_exampleid**](ExamplesApi.md#delete_api_projects_projectid_examples_exampleid) | **DELETE** /api/projects/{projectId}/examples/{exampleId} | 
[**get_api_projects_projectid_examples**](ExamplesApi.md#get_api_projects_projectid_examples) | **GET** /api/projects/{projectId}/examples | 
[**get_api_projects_projectid_examples_exampleid**](ExamplesApi.md#get_api_projects_projectid_examples_exampleid) | **GET** /api/projects/{projectId}/examples/{exampleId} | 
[**post_api_projects_projectid_examples**](ExamplesApi.md#post_api_projects_projectid_examples) | **POST** /api/projects/{projectId}/examples | 
[**put_api_projects_projectid_examples_exampleid**](ExamplesApi.md#put_api_projects_projectid_examples_exampleid) | **PUT** /api/projects/{projectId}/examples/{exampleId} | 


# **delete_api_projects_projectid_examples_exampleid**
> delete_api_projects_projectid_examples_exampleid(project_id, example_id)


Delete a specific **Example**.

#### Error Responses:
`404 Not Found` - If an **Example** with the specified `exampleId` associated with the given `projectId` does not exist.

`403 Forbidden` - If the user does not have permission to update this **Project**.

`403 Locked` - If the **Project** is locked.
  

### Example

* OAuth Authentication (oauth2Auth):

```python
import numind.openapi_client
from numind.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://nuextract.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = numind.openapi_client.Configuration(
    host = "https://nuextract.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with numind.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = numind.openapi_client.ExamplesApi(api_client)
    project_id = 'project_id_example' # str | Unique project identifier.
    example_id = 'example_id_example' # str | Unique example identifier.

    try:
        api_instance.delete_api_projects_projectid_examples_exampleid(project_id, example_id)
    except Exception as e:
        print("Exception when calling ExamplesApi->delete_api_projects_projectid_examples_exampleid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **str**| Unique project identifier. | 
 **example_id** | **str**| Unique example identifier. | 

### Return type

void (empty response body)

### Authorization

[oauth2Auth](../README.md#oauth2Auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |
**0** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_api_projects_projectid_examples**
> List[ExampleResponse] get_api_projects_projectid_examples(project_id)


Return a list of **Examples** associated to the specified **Project**.

#### Error Responses:
`404 Not Found` - If a **Project** with the specified `projectId` does not exist.

`403 Forbidden` - If the user does not have permission to view this **Project**.
  

### Example

* OAuth Authentication (oauth2Auth):

```python
import numind.openapi_client
from numind.models.example_response import ExampleResponse
from numind.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://nuextract.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = numind.openapi_client.Configuration(
    host = "https://nuextract.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with numind.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = numind.openapi_client.ExamplesApi(api_client)
    project_id = 'project_id_example' # str | Unique project identifier.

    try:
        api_response = api_instance.get_api_projects_projectid_examples(project_id)
        print("The response of ExamplesApi->get_api_projects_projectid_examples:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExamplesApi->get_api_projects_projectid_examples: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **str**| Unique project identifier. | 

### Return type

[**List[ExampleResponse]**](ExampleResponse.md)

### Authorization

[oauth2Auth](../README.md#oauth2Auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |
**0** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_api_projects_projectid_examples_exampleid**
> ExampleResponse get_api_projects_projectid_examples_exampleid(project_id, example_id)


Return a specific **Example**.

#### Error Responses:
`404 Not Found` - If an **Example** with the specified `exampleId` associated with the given `projectId` does not exist.

`403 Forbidden` - If the user does not have permission to view this **Project**.
  

### Example

* OAuth Authentication (oauth2Auth):

```python
import numind.openapi_client
from numind.models.example_response import ExampleResponse
from numind.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://nuextract.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = numind.openapi_client.Configuration(
    host = "https://nuextract.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with numind.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = numind.openapi_client.ExamplesApi(api_client)
    project_id = 'project_id_example' # str | Unique project identifier.
    example_id = 'example_id_example' # str | Unique example identifier.

    try:
        api_response = api_instance.get_api_projects_projectid_examples_exampleid(project_id, example_id)
        print("The response of ExamplesApi->get_api_projects_projectid_examples_exampleid:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExamplesApi->get_api_projects_projectid_examples_exampleid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **str**| Unique project identifier. | 
 **example_id** | **str**| Unique example identifier. | 

### Return type

[**ExampleResponse**](ExampleResponse.md)

### Authorization

[oauth2Auth](../README.md#oauth2Auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |
**0** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_api_projects_projectid_examples**
> ExampleResponse post_api_projects_projectid_examples(project_id, create_or_update_example_request)


Create a new **Example** associated with a specific **Project**.
An **Example** consists of an (input, output) pair, where the input is identified by a `documentId`, and the output represents the expected inference result.
To obtain a `documentId`, use the endpoints under the ***documents*** tag.
Once created, this **Example** will be automatically applied to subsequent inference calls as an example — unless the output no longer aligns with the current template.
In such cases, the **Example** will be skipped.



#### Effect:
 If the **Project** is a **Reference Project**, the **Document** used to create this **Example** will be automatically shared for read access to all users.

#### Response:
 The response contains `exampleId`, which is required to update or delete this **Example**.

#### Error Responses:
`404 Not Found` - If a **Project** with the specified `projectId` does not exist or a **Document** with the specified `documentId` does not exist.

`403 Forbidden` - If the user does not have permission to update this **Project** or use the specified **Document**.

`403 Locked` - If the **Project** is locked.
  

### Example

* OAuth Authentication (oauth2Auth):

```python
import numind.openapi_client
from numind.models.create_or_update_example_request import CreateOrUpdateExampleRequest
from numind.models.example_response import ExampleResponse
from numind.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://nuextract.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = numind.openapi_client.Configuration(
    host = "https://nuextract.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with numind.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = numind.openapi_client.ExamplesApi(api_client)
    project_id = 'project_id_example' # str | Unique project identifier.
    create_or_update_example_request = {"documentId":"449af2b9-a3e7-477b-a1c6-13d4d68fa7de","result":{"orderId":"Example: o-67214","customerId":"Example: c-76549","orderDate":"2024-04-05T08:20:00.000Z","status":"pending","totalAmount":89.75,"currency":"USD","items":[{"productId":"p-00567","quantity":1,"unitPrice":89.75}],"shippingAddress":{"street":"123 Elm St","city":"Boston","state":"MA","country":"USA","zip":"02108"},"comments":"Hold at pickup location.","deliveryPreferences":["scheduled_delivery","contactless_delivery"],"estimatedDelivery":"2024-04-10T19:00:00.000Z"}} # CreateOrUpdateExampleRequest | 

    try:
        api_response = api_instance.post_api_projects_projectid_examples(project_id, create_or_update_example_request)
        print("The response of ExamplesApi->post_api_projects_projectid_examples:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExamplesApi->post_api_projects_projectid_examples: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **str**| Unique project identifier. | 
 **create_or_update_example_request** | [**CreateOrUpdateExampleRequest**](CreateOrUpdateExampleRequest.md)|  | 

### Return type

[**ExampleResponse**](ExampleResponse.md)

### Authorization

[oauth2Auth](../README.md#oauth2Auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json, text/plain

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |
**400** | Invalid value for: body |  -  |
**0** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **put_api_projects_projectid_examples_exampleid**
> ExampleResponse put_api_projects_projectid_examples_exampleid(project_id, example_id, create_or_update_example_request)


Update a specific **Example**.

#### Error Responses:
`404 Not Found` - If an **Example** with the specified `exampleId` associated with the given `projectId` does not exist, or if a **Document** with the specified `documentId` cannot be found.

`403 Forbidden` - If the user does not have permission to update this **Project** or use the specified **Document**.

`403 Locked` - If the **Project** is locked.
  

### Example

* OAuth Authentication (oauth2Auth):

```python
import numind.openapi_client
from numind.models.create_or_update_example_request import CreateOrUpdateExampleRequest
from numind.models.example_response import ExampleResponse
from numind.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://nuextract.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = numind.openapi_client.Configuration(
    host = "https://nuextract.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with numind.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = numind.openapi_client.ExamplesApi(api_client)
    project_id = 'project_id_example' # str | Unique project identifier.
    example_id = 'example_id_example' # str | Unique example identifier.
    create_or_update_example_request = {documentId=449af2b9-a3e7-477b-a1c6-13d4d68fa7de, result={orderId=Example: o-67214, customerId=Example: c-76549, orderDate=2024-04-05T08:20:00.000Z, status=pending, totalAmount=89.75, currency=USD, items=[{productId=p-00567, quantity=1, unitPrice=89.75}], shippingAddress={street=123 Elm St, city=Boston, state=MA, country=USA, zip=02108}, comments=Hold at pickup location., deliveryPreferences=[scheduled_delivery, contactless_delivery], estimatedDelivery=2024-04-10T19:00:00.000Z}} # CreateOrUpdateExampleRequest | 

    try:
        api_response = api_instance.put_api_projects_projectid_examples_exampleid(project_id, example_id, create_or_update_example_request)
        print("The response of ExamplesApi->put_api_projects_projectid_examples_exampleid:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExamplesApi->put_api_projects_projectid_examples_exampleid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **str**| Unique project identifier. | 
 **example_id** | **str**| Unique example identifier. | 
 **create_or_update_example_request** | [**CreateOrUpdateExampleRequest**](CreateOrUpdateExampleRequest.md)|  | 

### Return type

[**ExampleResponse**](ExampleResponse.md)

### Authorization

[oauth2Auth](../README.md#oauth2Auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json, text/plain

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |
**400** | Invalid value for: body |  -  |
**0** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

