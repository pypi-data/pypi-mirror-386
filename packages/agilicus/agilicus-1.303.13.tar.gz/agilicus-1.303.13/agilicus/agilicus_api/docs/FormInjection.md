# FormInjection

Configuration specific to authenticate form injection 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**inject_credentials** | **bool** | Inject the username/password credentials into the http form.  | [optional] 
**username_field** | **str** | The field name used for mapping to a username.  | [optional]  if omitted the server will use the default value of "username"
**password_field** | **str** | The field name used for mapping to a password  | [optional]  if omitted the server will use the default value of "password"
**username_credential** | **str** | The credential for the username field  | [optional] 
**password_credential** | **str** | The credential for the password field  | [optional] 
**username_query_selector** | **str, none_type** | A query selector to run as argument to document.querySelector(), to find the  element associated with the username input.  | [optional] 
**password_query_selector** | **str, none_type** | A query selector to run as argument to document.querySelector(), to find the  element associated with the password input.  | [optional] 
**password_navigation_delay_ms** | **int, none_type** | A delay, in milliseconds, that delays the password input. This is required in situations where a navigation event occurs between username input and  password input.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


