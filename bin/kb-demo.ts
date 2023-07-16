#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { KbKendraStack } from '../lib/kendra-stack/kb-kendra-stack';
import { KbStreamlitAppStack } from '../lib/kb-streamlit-app'
import { open } from 'fs';

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
  const bedrockRoleARN = app.node.tryGetContext('bedrockRoleARN')
  if (bedrockRoleARN === undefined) {
    if (openAIAPIKey === undefined) {
      console.error('*** You must provide either a bedrockRoleArn or an openAIAPIKey')
      console.error('*** you can do this by editing cdk.context.json 🚀            ***')
      throw new Error("Missing bedrockRoleArn or openAIAPIKey")
    }
  }
  

  return {
    scrapeUrls,
    customerName,
    openAIAPIKey,
    customerFavicon,
    customerLogo,
    bedrockRoleARN
  }
}

const config = extractConfig();

console.log(`*** 🚀 Starting deployment for ${config.customerName} ***`)
console.log(`*** 🚀 Scraping ${config.scrapeUrls} ***`)

const kendaStack = new KbKendraStack(app, `KB-${config.customerName}-KendraStack`, {
  scrapeUrls: config.scrapeUrls,
});

new KbStreamlitAppStack (app, `KB-${config.customerName}-AppStack`, {
  kendraIndexId: kendaStack.kendraIndexId,
  openAIAPIKey: config.openAIAPIKey,
  customerName: config.customerName,
  customerFavicon: config.customerFavicon,
  customerLogo: config.customerLogo,
  bedrockRoleARN: config.bedrockRoleARN
})

