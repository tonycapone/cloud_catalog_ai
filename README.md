# Retrieval Augmented Generation Demo-In-A-Box

## Usage
Copy `cdk.context.json.template` to `cdk.context.json` and fill in the values.

Set [up cdk](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install) and [bootstrap your account](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html) if you haven't already.

Run `npm install` to install the dependencies.


Then run `cdk deploy --all` to deploy the project to your environment.

### Example Configuration
```
{
    "scrapeUrls": [
        "https://www.example.com/"
    ],
    "customerName": "ACME Corp",
    "openAIAPIKey": "OPENAI_API_KEY",
    "customerFavicon": "optional favicon link",
    "customerLogo": "optional logo link for chat avatar"

}
```
 The `scrapeUrls` array contains the URLs that will be scraped and indexed into Kendra.
 `customerName` Optional. This is the name of the customer that will be displayed in the header of the Streamlit Chat UI.
`CustomerFavicon` Optional. The favicon that will be displayed in the header of the Streamlit Chat UI.
`CustomerLogo` Optional. The logo that will be displayed next to generated responses.
`openAIAPIKey` is self explanatory

## Stack Description
### KendraStack
This stack creates a Kendra index. It also creates a Kendra datasource for the index and initiates a sync job to populate the datasource with the scraped URLs.

### KbStreamlitAppStack
This stack creates a Streamlit ChatBot app that interacts with the Kendra Index. 

