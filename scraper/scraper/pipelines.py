import boto3

class KendraPipeline:
    def open_spider(self, spider):
        self.kendra = boto3.client('kendra')

    def close_spider(self, spider):
        del self.kendra

    def process_item(self, item, spider):
        document = {
            'Title': item['title'],
            'Blob': bytes(' '.join(item['content']), 'utf-8'),
        }
        print(document)
        self.kendra.batch_put_document(
            IndexId='9f4b36a9-0945-41c1-b77c-9e80c42e6962',
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
