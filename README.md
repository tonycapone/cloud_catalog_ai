# Retrieval Augmented Generation Demo-In-A-Box

## Usage
Copy `cdk.context.json.template` to `cdk.context.json` and fill in the values.



Then run `cdk deploy` to deploy the stack.

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

## Useful commands


* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template
