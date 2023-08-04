import boto3
import os
class KendraPipeline:
    index_id = os.environ['KENDRA_INDEX_ID']
    def open_spider(self, spider):
        self.kendra = boto3.client('kendra')

    def close_spider(self, spider):
        del self.kendra

    def process_item(self, item, spider):
        if item['title'] is None:
            item['title'] = item['url']
        document = {
            'Title': item['title'],
            'Blob': item['content']
        }
        print(document)
        self.kendra.batch_put_document(
            IndexId=self.index_id,
            RoleArn='arn:aws:iam::543999415209:role/KB-JCPenny-KendraStack-KendraRole9C3D9CF0-RCLYOK6NFOEW',
            Documents=[{
                'Id': item['url'],
                'Title': item['title'],
                'Blob': document['Blob'],
                'ContentType': 'PLAIN_TEXT',
                'Attributes': [{
                    'Key': '_source_uri',
                    'Value': {
                        "StringValue": item['url']
                    }
                    
                }]
            }]
        )
        return item
