# arthur_client.api_bindings.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**health_check_api_health_get**](DefaultApi.md#health_check_api_health_get) | **GET** /api/health | Health Check


# **health_check_api_health_get**
> HealthStatus health_check_api_health_get()

Health Check

Confirms the API is healthy and responsive.

### Example


```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.health_status import HealthStatus
from arthur_client.api_bindings.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = arthur_client.api_bindings.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with arthur_client.api_bindings.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = arthur_client.api_bindings.DefaultApi(api_client)

    try:
        # Health Check
        api_response = api_instance.health_check_api_health_get()
        print("The response of DefaultApi->health_check_api_health_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->health_check_api_health_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**HealthStatus**](HealthStatus.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

