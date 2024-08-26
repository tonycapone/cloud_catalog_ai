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

def run_command(command):
    try:
        print("Running command: ", command)
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def deploy(args):
    check_context_file()
    command = "cdk deploy"
    if args.stack:
        command += f" {args.stack}"
    else:
        command += " --all"
    if args.profile:
        command += f" --profile {args.profile}"
    stack_name = args.stack if args.stack else "all"
    command += f" --require-approval never"
    print(f"*** 🚀 Deploying {stack_name} stack(s) ***")
    run_command(command)

def destroy(args):
    
    check_context_file()
    command = "cdk destroy"
    if args.stack:
        command += f" {args.stack}"
    else:
        command += " --all"
    if args.profile:
        command += f" --profile {args.profile}"
    stack_name = args.stack if args.stack else "all"
    print(f"*** 🚀 Destroying {stack_name} stack(s) ***")
    run_command(command)

def synth(args):
    check_context_file()
    command = "cdk synth"
    if args.stack:
        command += f" {args.stack}"
    if args.profile:
        command += f" --profile {args.profile}"
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

def main():
    check_cdk_cli()
    check_docker()

    parser = argparse.ArgumentParser(description="CDK Deployment Script")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy the CDK stack")
    deploy_parser.add_argument("--all", action="store_true", help="Deploy all stacks")
    deploy_parser.add_argument("--stack", choices=["app", "kb"], help="Deploy a specific stack (app or kb)")
    deploy_parser.add_argument("--profile", help="AWS profile to use")

    # Destroy command
    destroy_parser = subparsers.add_parser("destroy", help="Destroy the CDK stack")
    destroy_parser.add_argument("--all", action="store_true", help="Destroy all stacks")
    destroy_parser.add_argument("--stack", choices=["app", "kb"], help="Destroy a specific stack (app or kb)")
    destroy_parser.add_argument("--profile", help="AWS profile to use")

    # Synth command
    synth_parser = subparsers.add_parser("synth", help="Synthesize the CDK stack")
    synth_parser.add_argument("--stack", choices=["app", "kb"], help="Synthesize a specific stack (app or kb)")
    synth_parser.add_argument("--profile", help="AWS profile to use")

    args = parser.parse_args()

    if args.command == "deploy":
        deploy(args)
    elif args.command == "destroy":
        destroy(args)
    elif args.command == "synth":
        synth(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()