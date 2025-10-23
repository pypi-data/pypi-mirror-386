# DSDetailResultObject


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**urlf_report** | [**List[UrlfEntryObject]**](UrlfEntryObject.md) |  | [optional] 
**dlp_report** | [**DlpReportObject**](DlpReportObject.md) |  | [optional] 
**dbs_report** | [**List[DbsEntryObject]**](DbsEntryObject.md) |  | [optional] 
**tc_report** | [**TcReportObject**](TcReportObject.md) |  | [optional] 
**mc_report** | [**McReportObject**](McReportObject.md) |  | [optional] 
**agent_report** | [**AgentReportObject**](AgentReportObject.md) |  | [optional] 
**topic_guardrails_report** | [**TgReportObject**](TgReportObject.md) |  | [optional] 
**cg_report** | [**CgReportObject**](CgReportObject.md) |  | [optional] 

## Example

```python
from aisecurity.generated_openapi_client.models.ds_detail_result_object import DSDetailResultObject

# TODO update the JSON string below
json = "{}"
# create an instance of DSDetailResultObject from a JSON string
ds_detail_result_object_instance = DSDetailResultObject.from_json(json)
# print the JSON string representation of the object
print(DSDetailResultObject.to_json())

# convert the object into a dict
ds_detail_result_object_dict = ds_detail_result_object_instance.to_dict()
# create an instance of DSDetailResultObject from a dict
ds_detail_result_object_from_dict = DSDetailResultObject.from_dict(ds_detail_result_object_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


