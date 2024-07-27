# Copyright 2024, Clumio Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto3
from botocore.exceptions import ClientError
from clumio_sdk_v9 import ClumioConnectAccount, AWSOrgAccount, ListEC2Instance, EnvironmentId, RestoreEC2, EC2BackupList, EBSBackupList, RestoreEBS, OnDemandBackupEC2


def lambda_handler(events, context):

    target_region = events.get('target_region',None)
    target_account = events.get('target_account', None)
    target_role_arn = events.get('target_role_arn', None)
    run_token = events.get('inputs',{}).get('run_token', None)

    # usage:
    aws_account_mng = AWSOrgAccount()
    inputs = {
        'scan_id': None,
        'instance_id': None
    }
    [status, msg, cred] = aws_account_mng.connect_assume_role("boto3", target_role_arn, 'a')
    if not status:
        return {"status": 407, "msg": msg, "account_id": target_account, "regions": [], "services": []}

    AccessKeyId = cred.get("AccessKeyId", None)
    SecretAccessKey = cred.get('SecretAccessKey', None)
    SessionToken = cred.get('SessionToken', None)
    try:
        aws_session1 = boto3.Session(
            aws_access_key_id=AccessKeyId,
            aws_secret_access_key=SecretAccessKey,
            aws_session_token=SessionToken,
            region_name=target_region
        )
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"failed to initiate session {error}"
        return {"status": 401, "msg": error_msg, "inputs": inputs}
    client_ec2 = aws_session1.client('ec2')
    try:
        desc_instance = client_ec2.describe_instances(
            Filters=[
                {
                    'Name': 'tag:ClumioTaskToken',
                    'Values': [run_token],
                },
            ],
        )
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"failed to run describe instances {error}"
        return {"status": 402, "msg": error_msg, "inputs": inputs}
    new_instance_id = desc_instance.get('Reservations', [])[0].get('Instances', [])[0].get('InstanceId', None)
    print(new_instance_id)
    client_guard = aws_session1.client('guardduty')
    try:
        start_scan_rsp = client_guard.start_malware_scan(
            ResourceArn=f'arn:aws:ec2:{target_region}:{target_account}:instance/{new_instance_id}'
        )
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"failed to start scan {error}"
        return {"status": 403, "msg": error_msg, "inputs": inputs}
    print(start_scan_rsp)
    scan_id = start_scan_rsp.get('ScanId', None)
    inputs = {
        'scan_id': scan_id,
        'instance_id': new_instance_id
    }
    return {"status": 201, "msg": "initiated scan",
            "inputs": inputs}