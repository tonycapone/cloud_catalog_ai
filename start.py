#!/usr/bin/env python3
import argparse
import subprocess
import sys
import json
import os
import shutil

def check_cdk_cli():
    if shutil.which('cdk') is None:
        print("CDK CLI is not found in your system PATH.")
        print("Please install the AWS CDK CLI by following the instructions at:")
        print("https://docs.aws.amazon.com/cdk/v2/guide/cli.html")
        print("After installation, restart your terminal and run this script again.")
        sys.exit(1)

def check_docker():
    if shutil.which('docker') is None:
        print("Docker is not found in your system PATH.")
        print("Please install Docker by following the instructions at:")
        print("https://docs.docker.com/get-docker/")
        print("After installation, restart your terminal and run this script again.")
        sys.exit(1)
        
def check_ecr_login():
    try:
        # Check if we're logged in to ECR Public
        result = subprocess.run(["docker", "image", "ls", "public.ecr.aws/z6v3b4o4/aws-cli"], capture_output=True, text=True)
        if "REPOSITORY" in result.stdout:
            print("Already logged in to ECR Public.")
        else:
            print("Logging in to ECR Public...")
            login_command = "aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/z6v3b4o4"
            subprocess.run(login_command, shell=True, check=True)
            print("Successfully logged in to ECR Public.")
    except subprocess.CalledProcessError as e:
        print(f"Error logging in to ECR Public: {e}")
        sys.exit(1)

def run_command(command):
    try:
        print("Running command: ", command)
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def deploy(stack=None):
    context = load_context()
    command = "cdk deploy"
    if stack:
        if stack == "app":
            stack_name = f"KB-{context['customerName']}-AppStack"
        elif stack == "kb":
            stack_name = f"KB-{context['customerName']}-KBStack"
        else:
            print("Invalid stack option. Please choose 'app' or 'kb'.")
            return
        command += f" {stack_name}"
    else:
        command += " --all"
    command += " --require-approval never"
    print(f"*** 🚀 Deploying {'all stacks' if not stack else stack} ***")
    run_command(command)

def destroy(stack=None):
    context = load_context()
    command = "cdk destroy"
    if stack:
        if stack == "app":
            stack_name = f"KB-{context['customerName']}-AppStack"
        elif stack == "kb":
            stack_name = f"KB-{context['customerName']}-KBStack"
        else:
            print("Invalid stack option. Please choose 'app' or 'kb'.")
            return
        command += f" {stack_name}"
    else:
        command += " --all"
    print(f"*** 🚀 Destroying {'all stacks' if not stack else stack} ***")
    run_command(command)

def synth(stack=None):
    command = "cdk synth"
    if stack:
        command += f" {stack}"
    run_command(command)

def check_context_file():
    context_file = 'cdk.context.json'
    required_keys = ['scrapeUrls', 'customerName', 'customerIndustry']
    optional_keys = ['customerLogo', 'customerFavicon']
    
    if not os.path.exists(context_file) or os.path.getsize(context_file) == 0:
        print("*** ⛔️ cdk.context.json is missing or empty. Let's set it up! ***")
        create_context_file({})
    else:
        with open(context_file, 'r') as f:
            context = json.load(f)
        if not all(key in context and context[key] for key in required_keys):
            print("*** ⛔️ cdk.context.json is incomplete. Let's update it! ***")
            create_context_file(context)

def create_context_file(existing_context):
    context = existing_context.copy()
    
    def get_input(key, prompt, required=True):
        existing_value = context.get(key, '')
        prompt_with_default = f"{prompt} ({existing_value}): " if existing_value else f"{prompt}: "
        while True:
            value = input(prompt_with_default).strip() or existing_value
            if value or not required:
                return value
            print("This field is required. Please enter a value.")

    context['scrapeUrls'] = get_input('scrapeUrls', "Enter comma-separated URLs to scrape").split(',')
    context['customerName'] = get_input('customerName', "Enter customer name")
    context['customerIndustry'] = get_input('customerIndustry', "Enter customer industry")
    context['customerLogo'] = get_input('customerLogo', "Enter customer logo URL (optional)", required=False)
    context['customerFavicon'] = get_input('customerFavicon', "Enter customer favicon URL (optional)", required=False)

    with open('cdk.context.json', 'w') as f:
        json.dump(context, f, indent=2)
    print("cdk.context.json has been created/updated successfully!")

def load_context():
    with open('cdk.context.json', 'r') as f:
        return json.load(f)

def main():
    check_cdk_cli()
    check_docker()
    check_context_file()

    parser = argparse.ArgumentParser(description="CDK Deployment Script")
    parser.add_argument("command", choices=["deploy", "destroy", "synth"], help="Command to execute")
    parser.add_argument("stack", nargs="?", choices=["app", "kb"], help="Stack to operate on (optional)")

    args = parser.parse_args()

    if args.command == "deploy":
        deploy(args.stack)
    elif args.command == "destroy":
        destroy(args.stack)
    elif args.command == "synth":
        synth(args.stack)

if __name__ == "__main__":
    main()