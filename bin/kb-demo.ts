#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { KbStreamlitAppStack } from '../lib/kb-streamlit-app'
import { KBStack } from '../lib/kb-stack/br-kb-stack'; 

const app = new cdk.App();

/**
 * Check if cdk context is defined either by context file or command line flags
 * If the context file is missing return a 
 */


const extractConfig = () => {
  const scrapeUrls = app.node.tryGetContext('scrapeUrls')
  
  if (scrapeUrls === undefined) {
    console.warn('*** ⛔️ WARNING: You must provide a valid scrapeUrl   ***')
    console.warn('*** you can do this by editing cdk.context.json 🚀            ***')
    throw new Error("Missing scrapeUrls")
  } 
  const customerName = app.node.tryGetContext('customerName')
  if (customerName === undefined) {
    console.warn('*** ⛔️ WARNING: You must provide a valid customerName   ***')
    console.warn('*** you can do this by editing cdk.context.json 🚀            ***')
    throw new Error("Missing customerName")
  }
  const openAIAPIKey = app.node.tryGetContext('openAIAPIKey')
  const customerFavicon = app.node.tryGetContext('customerFavicon')
  if (customerFavicon === undefined) {
    console.info('*** customerFavicon is missing   ***')
    console.info('*** you can do this by editing cdk.context.json 🚀            ***')
  }
  const customerLogo = app.node.tryGetContext('customerLogo')
  if (customerLogo === undefined) {
    console.info('*** customerLogo is missing   ***')
    console.info('*** you can do this by editing cdk.context.json 🚀            ***')
  }
  const customerIndustry = app.node.tryGetContext('customerIndustry')
  if (customerIndustry === undefined) {
    console.warn('*** ⛔️ WARNING: You must provide a valid customerIndustry   ***')
    console.warn('*** you can do this by editing cdk.context.json 🚀            ***')
    throw new Error("Missing customerIndustry")
  }
  

  return {
    scrapeUrls,
    customerName,
    openAIAPIKey,
    customerFavicon,
    customerLogo,
    customerIndustry
  }
}

const config = extractConfig();

// remove any special characters from the stack name
let stackPrefix = config.customerName
stackPrefix = "KB-" + stackPrefix.replace(/[^\w]/g, '');

const kbStack = new KBStack(app, `${stackPrefix}-KBStack`, {
  scrapeUrls: (config.scrapeUrls + "").split(","),
});

new KbStreamlitAppStack (app, `${stackPrefix}-AppStack`, {
  knowledgeBaseId: kbStack.knowledgeBaseId,
  openAIAPIKey: config.openAIAPIKey,
  customerName: config.customerName,
  customerFavicon: config.customerFavicon,
  customerLogo: config.customerLogo,
  customerIndustry: config.customerIndustry
})

