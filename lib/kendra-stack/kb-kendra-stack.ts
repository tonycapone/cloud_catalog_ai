import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path'
import {
  aws_kendra as kendra,
  CustomResource,
  aws_iam as iam,
  aws_s3 as s3,
  aws_lambda as lambda,
  aws_logs as logs,
  custom_resources as cr
} from 'aws-cdk-lib'

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
      name: this.node.tryGetContext('customerName') + '-KendraIndex',
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
            crawlDepth: 4,
            maxLinksPerPage: 100,
            maxContentSizePerPageInMegaBytes: 50,
            maxUrlsPerMinuteCrawlRate: 100,
          }

        }
      }
      )
      const kendraLambda = new lambda.Function(this, 'startDSSyncLambda', {
        runtime: lambda.Runtime.PYTHON_3_9,
        architecture: lambda.Architecture.ARM_64,
        code: lambda.Code.fromAsset(path.join(__dirname, './lambda')),
        handler: 'run_sync.lambda_handler',
        initialPolicy: [
          new iam.PolicyStatement({ actions: ['kendra:*'], resources: ['*'] }),
        ],
      });

      const kendraLambdaProvider = new cr.Provider(this, 'kendraDSProvider', {
        onEventHandler: kendraLambda,
        logRetention: logs.RetentionDays.ONE_DAY,
      });

      new CustomResource(this, 'kendraDSCustomResource', {
        serviceToken: kendraLambdaProvider.serviceToken,
        properties: {
          IndexId: kendraIndex.ref,
          DataSourceId: kendraDataSource.ref,
        }
      });
    }

  }

}


