

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as iam from 'aws-cdk-lib/aws-iam';

interface KbStreamlitAppStackProps extends cdk.StackProps {
    kendraIndexId: string;
}
class KbStreamlitAppStack extends cdk.Stack {

    constructor(scope: Construct, id: string, props?: KbStreamlitAppStackProps) {
        super(scope, id, props);
        const vpc = new ec2.Vpc(
            this, "ZephStreamlitVPC",
            {
                maxAzs: 2
            }
        )
        const cluster = new ecs.Cluster(this, "ZephStreamlitCluster", {
            vpc: vpc
        })

        // Create a role
        const taskRole = new iam.Role(this, 'TaskRole', {
            assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        });
            // Add necessary permissions to the role
        taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'));
        taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonKendraFullAccess'));


        // Add necessary permissions to the role
        taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3FullAccess'));
        const image = ecs.ContainerImage.fromAsset('lib/streamlit-docker')
        const fargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(this, "ZephFargateService", {
            cluster: cluster,
            cpu: 256,

            desiredCount: 1,
            taskImageOptions: {
                image: image,
                taskRole,
                environment: {
                    "OPENAI_API_KEY": "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",
                    "KENDRA_INDEX_ID": props?.kendraIndexId || "KendraIndex"
                },
                containerPort: 8501

            },
            memoryLimitMiB: 512,
            publicLoadBalancer: true



        })

    }
}
export { KbStreamlitAppStack }