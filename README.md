# Retrieval Augmented Generation Demo-In-A-Box
## About
This project is an easily deployable demo-in-a-box that demonstrates how to use the [Retrieval Augmented Generation](https://arxiv.org/abs/2005.11401) model to build a Generative AI chatbot that can answer questions about a customer's website. It uses [Amazon Kendra](https://aws.amazon.com/kendra/) to index the website and [Amazon Bedrock](https://aws.amazon.com/bedrock/) to generate responses to questions. It also uses [Streamlit](https://www.streamlit.io/) to provide a web interface for the chatbot.

See the [this quip](https://quip-amazon.com/pI57Abo7dElG/Enterprise-Knowledge-Base-Chatbot-Demo) for more information. 

__Note: You must have access to a Bedrock enabled account to use this demo. You can also use the OpenAI API instead of Bedrock, but it's not advisable to demo in this way to customers.__

## Deployment
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
    "bedrockRoleArn": "arn:aws:iam::123456789012:role/bedrock-role",
    "customerLogo": "optional logo link for chat avatar"

}
```
The `scrapeUrls` array contains the URLs that will be scraped and indexed into Kendra.

`customerName` Optional. This is the name of the customer that will be displayed in the header of the Streamlit Chat UI.

`customerFavicon` Optional. The favicon that will be displayed in the header of the Streamlit Chat UI.

`customerLogo` Optional. The logo that will be displayed next to generated responses.

You must also specify one of:
`bedrockRoleArn` The ARN of a role that has access to the Bedrock API.

or
`openaiApiKey` An API key for the OpenAI API.


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
OPENAI_API_KEY or BEDROCK_ASSUME_ROLE_ARN
```
Then run `streamlit run main.py` to start the app.
