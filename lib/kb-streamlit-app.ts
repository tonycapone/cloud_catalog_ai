

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as iam from 'aws-cdk-lib/aws-iam';

interface KbStreamlitAppStackProps extends cdk.StackProps {
    kendraIndexId: string;
    openAIAPIKey?: string;
    customerName: string;
    customerFavicon: string;
    customerLogo: string;
    customerIndustry: string;
}
class KbStreamlitAppStack extends cdk.Stack {

    constructor(scope: Construct, id: string, props: KbStreamlitAppStackProps) {
        super(scope, id, props);
        const vpc = new ec2.Vpc(
            this, "StreamlitVPC",
            {
                maxAzs: 2
            }
        )
        const cluster = new ecs.Cluster(this, "StreamlitCluster", {
            vpc: vpc
        })

        // Create a role
        const taskRole = new iam.Role(this, 'TaskRole', {
            assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        });
        // Add necessary permissions to the role
        taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'));
        taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonKendraFullAccess'));
        taskRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            resources: ['*'],
            actions: [
                'bedrock:*'
            ]
        }))

        // Add necessary permissions to the role
        taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'));
        const image = ecs.ContainerImage.fromAsset('lib/streamlit-docker', {
            platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64
        })
        const fargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(this, "StreamlitFargateService", {
            cluster: cluster,
            cpu: 256,
            desiredCount: 1,
            taskImageOptions: {
                image: image,
                taskRole,
                environment: {
                    "OPENAI_API_KEY": props.openAIAPIKey || "",
                    "KENDRA_INDEX_ID": props.kendraIndexId,
                    "CUSTOMER_NAME": props.customerName,
                    "FAVICON_URL": props.customerFavicon,
                    "LOGO_URL": props.customerLogo,
                    "CUSTOMER_INDUSTRY": props.customerIndustry
                },
                containerPort: 8501
            },
            
            memoryLimitMiB: 512,
            publicLoadBalancer: true
        })

    }
}
export { KbStreamlitAppStack }