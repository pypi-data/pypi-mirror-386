import boto3
import argparse

def get_instance_name(instance):
    # Tags is a list of dicts with 'Key' and 'Value'
    for tag in instance.get('Tags', []):
        if tag['Key'] == 'Name':
            return tag['Value']
    return 'N/A'

def list_ec2_instances(region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            print("Instance ID:", instance['InstanceId'])
            print("Type:", instance['InstanceType'])
            print("State:", instance['State']['Name'])
            print("Public IP:", instance.get('PublicIpAddress', 'N/A'))
            print("Name:", get_instance_name(instance))
            print("---")

def main(argv=None):
    parser = argparse.ArgumentParser(description="AWS EC2 CLI Tool")
    parser.add_argument('--list-instances', action='store_true', help='List EC2 instances')
    parser.add_argument('--region', type=str, default='eu-north-1', help='AWS region (default: eu-north-1)')
    args = parser.parse_args(argv)

    if args.list_instances:
        list_ec2_instances(args.region)
    else:
        print("No action specified; use --list-instances to list EC2 instances.")

if __name__ == "__main__":
    main()
