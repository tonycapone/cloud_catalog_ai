# Generative AI Tailored Demos
## About
The GenAI Tailored Demo Experience is a tool designed to introduce customers to Generative AI, targeting customers in the "just curious" or FOMO stage of their journey. The demo can be customized to each customer and their industry, and consists of three main components: a Conversational AI Chat Demo, a Product Ideator, and a Data Querying Tool. 

Each part serves a distinct purpose, demonstrating practical applications of GenAI by utilizing real data from the customer's public-facing website. Deployed as an easily manageable CDK project, the demo experience emphasizes the real-world potential of GenAI in a way that resonates with the specific needs and context of the customer.

This tailored approach not only personalizes the experience but also highlights the transformative potential of GenAI, instilling confidence, curiosity, and recognition of the vast opportunities that Generative AI presents.

The chatbot portion demonstrates how to use [Retrieval Augmented Generation (RAG)](https://arxiv.org/abs/2005.11401) to build a Generative AI chatbot that can answer questions about a customer's website. It uses the [Amazon Bedrock Knowledge Base](https://aws.amazon.com/bedrock/knowledge-bases/) webcrawling datasource to index the website and generate responses to questions. It also uses [Streamlit](https://www.streamlit.io/) to provide a web interface for the chatbot.


See the [this quip](https://quip-amazon.com/pI57Abo7dElG/Enterprise-Knowledge-Base-Chatbot-Demo) for more information. 

__Note: You must have access to a Bedrock enabled account to use this demo. You can also use the OpenAI API instead of Bedrock, but it's not advisable to demo in this way to customers.__

## Requirements
- A Bedrock enabled Isengard account
- AWS CDK installed locally
- Docker installed locally
- AWS CLI installed locally
- A CDK bootstrapped account (see instructions below)

## Deployment
__🆕 NEW! We now have a `start.py` script to help you deploy the project more easily.__

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
    "customerFavicon": "optional favicon link",
    "customerLogo": "http://acmecorp.com/logo.jpg",
    "customerIndustry": "Trucking"

}
```
The `scrapeUrls` array contains the URLs that will be scraped and indexed into Kendra. Typically this is the customer's website. 

`customerName` This is the name of the customer that will be displayed in the header of the Streamlit Chat UI.

`customerFavicon` Optional - The favicon that will be displayed in the header of the Streamlit Chat UI.

`customerLogo` The logo that will be displayed next to generated responses.

`customerIndustry` The industry that the customer is in. Used for synthetic data generation

## Stack Description
### KendraStack
This stack creates a Kendra index. It also creates a Kendra datasource for the index and initiates a sync job to populate the datasource with the scraped URLs.

### KbStreamlitAppStack
This stack creates a Streamlit ChatBot app that interacts with the Kendra Index. 

## Local Development
To deploy the Streamlit app locally, cd to `/lib/streamlit-docker`. You must define the following environment variables:
```
KENDRA_INDEX_ID
CUSTOMER_NAME
LOGO_URL
FAVICON_URL
AWS_REGION
```
Then run `streamlit run main.py` to start the app.

## Scraping
The project uses the V1 verson of the Kendra web-scraper to crawl the customer's URLs. This works in most cases, but there are some situations where the scraper is blocked from some reason. In this case, you can use the provided scraper to crawl the customer's website and upload the results to Kendra.

The scraper uses a Python library called [Scrapy](https://scrapy.org/).

To use the scraper, cd to `/scraper` and run 

`pip install -r requirements.txt` 

to install the dependencies. Export the Kendra Index Id from your Kendra stack to the `KENDRA_INDEX_ID` environment variable. 

Then run 

`crapy crawl defaultspider`