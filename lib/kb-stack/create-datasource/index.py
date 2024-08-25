import boto3
import json
import cfnresponse

bedrock_agent = boto3.client('bedrock-agent')

def lambda_handler(event, context):
    if event['RequestType'] == 'Create':
        return create_data_source(event, context)
    elif event['RequestType'] == 'Delete':
        return delete_data_source(event, context)

def create_data_source(event, context):
    try:
        props = event['ResourceProperties']
        knowledge_base_id = props['knowledgeBaseId']
        urls = [{"url": url} for url in props['urls']]
        print(urls)
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=knowledge_base_id,
            name='WebCrawlerDataSource',
            description='Web crawler data source for Bedrock Knowledge Base',
            dataSourceConfiguration={
                'type': 'WEB',
                'webConfiguration': {
                    'crawlerConfiguration': {
                        'crawlerLimits': {
                            'rateLimit': 300  # Max rate, adjust as needed
                        },
                        'scope': 'HOST_ONLY'  # Adjust scope as needed
                    },
                    'sourceConfiguration': {
                        'urlConfiguration': {
                            'seedUrls': urls
                        }
                    }
                }
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {
                        'maxTokens': 1000,  # Adjust as needed
                        'overlapPercentage': 20  # Adjust as needed
                    }
                }
            }
        )

        data_source_id = response['dataSource']['dataSourceId']
        status = response['dataSource']['status']
        print(response)
        
        if status != 'AVAILABLE':
            failure_reasons = response['dataSource'].get('failureReasons', [])
            if failure_reasons:
                raise Exception(f"Data source creation failed. Reasons: {', '.join(failure_reasons)}")

        return {
            'Status': 'SUCCESS',
            'PhysicalResourceId': data_source_id,
            'Data': {
                'dataSourceId': data_source_id
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e
def delete_data_source(event, context):
    try:
        knowledge_base_id = event['ResourceProperties']['knowledgeBaseId']
        data_source_id = event['PhysicalResourceId']
        bedrock_agent.delete_data_source(knowledgeBaseId=knowledge_base_id, dataSourceId=data_source_id)
        return {
            'Status': 'SUCCESS',
            'Data': {}
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e