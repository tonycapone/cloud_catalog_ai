# Amazon Bedrock Insights Explorer: GenAI Demo Suite
## About
The Amazon Bedrock Insights Explorer is designed to showcase the capabilities of Amazon Bedrock, Bedrock Knowledge Bases, and advanced language models like Claude 3. This demo consists of two main components: a Conversational AI Chat Demo and an Automated Product Catalog Generator.

Each part demonstrates practical applications of Generative AI by utilizing real data from a public-facing website. Deployed as an easily manageable CDK project, the demo experience emphasizes the real-world potential of GenAI in various industries and use cases.

The chatbot portion demonstrates how to use [Retrieval Augmented Generation (RAG)](https://arxiv.org/abs/2005.11401) to build a Generative AI chatbot that can answer questions about a specific website. It leverages the [Amazon Bedrock Knowledge Base](https://aws.amazon.com/bedrock/knowledge-bases/) webcrawling datasource to index the website and generate responses to questions. A React.js app provides a web interface for the chatbot.

The Automated Product Catalog Generator is a feature that:
- Crawls website pages and extracts product information
- Uses Claude 3to categorize products and generate descriptions
- Stores data in Amazon DynamoDB for easy retrieval

## Requirements
- AWS Account
- AWS CDK installed locally
- Docker installed locally
- AWS CLI installed locally
- A CDK bootstrapped account (see instructions below)

## Deployment
### Using start.py

1. Make sure you have Python 3 installed on your system.

2. The `start.py` script should already be executable. To deploy the project:

   On Unix-like systems (Linux, macOS):
   ```
   ./start.py deploy
   ```
   
   On Windows:
   ```
   python start.py deploy
   ```

   This will check for CDK CLI installation, ensure your `cdk.context.json` is properly configured, and then deploy the default stack.

3. If you want to deploy a specific stack, you can add the `--stack` flag:
   ```
   ./start.py deploy --stack <stack-name>
   ```

4. If you want to use a specific AWS profile, you can add the `--profile` flag:
   ```
   ./start.py deploy --profile your-profile-name
   ```

5. To synthesize the CloudFormation template without deploying, run:
   ```
   ./start.py synth
   ```

6. To destroy the stacks, run:
   ```
   ./start.py destroy
   ```
   Or to destroy all stacks:
   ```
   ./start.py destroy --all
   ```

The `start.py` script will guide you through setting up the `cdk.context.json` file if it's missing or incomplete.

### Manual CDK Deployment (Alternative Method)

If you prefer to use CDK directly, you can still follow these steps:

Run `npm install` to install the dependencies.

Copy `cdk.context.json.template` to `cdk.context.json` and fill in the values.

Set [up cdk](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install) and [bootstrap your account](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html) if you haven't already.

Then run `cdk deploy --all` to deploy the project to your environment.

### Example Configuration for cdk.context.json
```
{
    "scrapeUrls": [
        "https://www.example.com/"
    ],
    "customerName": "ACME Corp",
    "customerIndustry": "Trucking"

}
```
The `scrapeUrls` array contains the URLs that will be scraped and indexed into Kendra. Typically this is the customer's website. 

`customerName` This is the name of the customer that will be displayed in the header of the Streamlit Chat UI.

`customerFavicon` Optional - The favicon that will be displayed in the header of the Streamlit Chat UI.

`customerLogo` The logo that will be displayed next to generated responses.

`customerIndustry` The industry that the customer is in. Used for synthetic data generation

## Stack Description

### KBStack (br-kb-stack.ts)
This stack creates the core components for the Bedrock Knowledge Base:

- OpenSearch Serverless Collection: Used for vector search capabilities.
- Bedrock Knowledge Base: Configured with the OpenSearch Serverless backend.
- Data Source: Created and linked to the Knowledge Base, using provided URLs for web crawling.
- Ingestion Job: Initiated to populate the Knowledge Base with data from the specified URLs.

### AppStack (app-stack.ts)
This stack deploys the application infrastructure:

- Backend Service: An ECS Fargate service running a containerized backend application.
- Frontend: A React application deployed to an S3 bucket.
- CloudFront Distribution: Serves the frontend and routes API requests to the backend.
- DynamoDB Table: Stores product information for the knowledge base.

## Local Development

### Backend
To run the backend service locally:

1. Navigate to the `lib/backend` directory.
2. Ensure Python 3.x is installed.
3. Set up the following environment variables (using a .env file or export in your terminal):
   ```
   AWS_REGION
   CUSTOMER_NAME
   KNOWLEDGE_BASE_ID
   PRODUCT_TABLE_NAME
   ```
4. Install dependencies: `pip install -r requirements.txt` (assuming there's a requirements.txt file)
5. Start the service by running:
   ```
   python app.py
   ```

### Frontend
To run the frontend locally:

1. Navigate to the `lib/frontend` directory.
2. Ensure Node.js (version 14.x or later) is installed.
3. Install dependencies: `npm install`
4. Start the development server: `npm start`

Note: When running locally, you may need to configure the frontend to point to your local or deployed backend service. Check the frontend configuration files for API endpoint settings.