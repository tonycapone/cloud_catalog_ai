import boto3

kendra = boto3.client('kendra')

def lambda_handler(event, context):
    request_type = event['RequestType']
    if request_type == 'Create': return on_create(event)

def on_create(event):
    props = event["ResourceProperties"]
    print("create new resource with props %s" % props)
    
    index_id = props["IndexId"]
    #split the data source id on the | character

    data_source_id = props["DataSourceId"].split("|")[0]
    print("data source id: %s" % data_source_id)

    sync_job = kendra.start_data_source_sync_job(
        Id=data_source_id,
        IndexId=index_id,
    )
    return {"PhysicalResourceId": sync_job["ExecutionId"]}