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
from clumio_sdk_v9 import ClumioConnectAccount, AWSOrgAccount, ListEC2Instance, EnvironmentId, RestoreEC2, \
    EC2BackupList, EBSBackupList, RestoreEBS, OnDemandBackupEC2


def lambda_handler(events, context):
    target_region = events.get('target_region', None)
    target_account = events.get('target_account', None)
    target_role_arn = events.get('target_role_arn', None)
    instance_id = events.get('inputs', {}).get('instance_id', None)
    scan_results = events.get('inputs', {}).get('scan_results', None)

    # usage:
    aws_account_mng = AWSOrgAccount()
    cred = aws_account_mng.connect_assume_role("boto3", target_role_arn, 'a')
    inputs = {
        'instance_id': instance_id,
        'scan_results': scan_results,
        'target_account': target_account,
        'target_region': target_region
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

        return {"status": 401, "msg": f"assume role failure {error_msg}","inputs": inputs}
    client_ec2 = aws_session1.client('ec2')

    if scan_results == 'CLEAN':
        try:
            change_tag_status = client_ec2.create_tags(
                Resources=[
                    instance_id,
                ],
                Tags=[
                    {
                        'Key': 'InstanceToScanStatus',
                        'Value': scan_results,
                    },
                ],
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to initiate session {error}"

            return {"status": 402, "msg": f"add/update tag failure {error_msg}","inputs": inputs}
        return {"status": 200, "msg": f"scan complete {scan_results}","inputs": inputs}
    else:
        return {"status": 205, "msg": f"scan complete {scan_results}","inputs": inputs}
