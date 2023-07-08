import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as kendra from 'aws-cdk-lib/aws-kendra';
import * as iam from 'aws-cdk-lib/aws-iam';



interface KbKendraStackProps extends cdk.StackProps {
  scrapeUrls?: string[];
}

export class KbKendraStack extends cdk.Stack {
  public readonly kendraIndexId: string;


  constructor(scope: Construct, id: string, props: KbKendraStackProps) {
    super(scope, id, props);


    // create Kendra Role
    const kendraRole = new iam.Role(this, 'KendraRole', {
      assumedBy: new iam.ServicePrincipal('kendra.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3ReadOnlyAccess'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonKendraFullAccess'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchLogsFullAccess'),
      ]
    }
    )
    // Initizalize Kendra Index
    const kendraIndex = new kendra.CfnIndex(this, 'KendraIndex', {
      name: 'KendraIndex',
      edition: 'DEVELOPER_EDITION',
      roleArn: kendraRole.roleArn,
    });

    this.kendraIndexId = kendraIndex.ref;

    if (props.scrapeUrls) {
      // Initialize Kendra Data Source Web Crawler V1
      const kendraDataSource = new kendra.CfnDataSource(this, 'KendraDataSource', {
        name: 'KendraDataSource',
        indexId: kendraIndex.ref,
        roleArn: kendraRole.roleArn,
        type: 'WEBCRAWLER',
        dataSourceConfiguration: {
          webCrawlerConfiguration: {

            urls: {
              seedUrlConfiguration: {
                seedUrls: props.scrapeUrls,
              }
            },
            crawlDepth: 3,
            maxLinksPerPage: 100,
            maxContentSizePerPageInMegaBytes: 50,
            maxUrlsPerMinuteCrawlRate: 100,
          }

        }
      }
      )
    }

  }

}
