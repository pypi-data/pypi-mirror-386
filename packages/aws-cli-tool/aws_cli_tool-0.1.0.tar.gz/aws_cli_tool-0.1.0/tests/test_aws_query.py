import pytest
from moto import mock_aws
import boto3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import aws_query

# ---------- Unit Test ----------
@mock_aws()
def test_list_ec2_instances_prints_instance(capsys):
    # Set up a fake EC2 instance
    ec2 = boto3.resource('ec2', region_name='eu-north-1')
    instance = ec2.create_instances(ImageId='ami-792394825386', MinCount=1, MaxCount=1)[0]
    instance_id = instance.id

    # Run the function under test
    aws_query.list_ec2_instances('eu-north-1')
    captured = capsys.readouterr()
    assert "Instance ID:" in captured.out
    assert instance_id in captured.out
    assert "State:" in captured.out

# ---------- Integration Test ----------
@mock_aws()
def test_cli_lists_instances(capsys):
    # Set up a fake EC2 instance
    ec2 = boto3.resource('ec2', region_name='eu-north-1')
    instance = ec2.create_instances(ImageId='ami-792394825386', MinCount=1, MaxCount=1)[0]
    instance_id = instance.id

    # Simulate CLI call in-process (Moto's mock works!)
    aws_query.main(['--list-instances', '--region', 'eu-north-1'])
    captured = capsys.readouterr()
    assert "Instance ID:" in captured.out
    assert instance_id in captured.out
