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
import re


def lambda_handler(events, context):

    target_region = events.get('target_region',None)
    target_account = events.get('target_account', None)
    target_role_arn = events.get('target_role_arn', None)
    scan_id = events.get('inputs',{}).get('scan_id', None)
    instance_id = events.get('inputs',{}).get('instance_id', None)


    # usage:
    aws_account_mng = AWSOrgAccount()

    inputs = {
        'scan_id': None,
        'instance_id': None,
        'scan_results': None
    }
    scan_status = None
    [status, msg, cred] = aws_account_mng.connect_assume_role("boto3", target_role_arn, 'a')
    if not status:
        return {"status": 407, "msg": msg, "account_id": target_account, "regions": [], "services": []}

    AccessKeyId = cred.get("AccessKeyId", None)
    SecretAccessKey = cred.get('SecretAccessKey', None)
    SessionToken = cred.get('SessionToken', None)
    # region = AWSDumpBucketRegion
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
    client_guard = aws_session1.client('guardduty')
    try:
        detector_rsp = client_guard.list_detectors()
    except ClientError as e:
        error = e.response['Error']['Code']
        error_msg = f"failed to run list detectors {error}"
        return {"status": 402, "msg": error_msg, "inputs": inputs}
    print(f"detector response {detector_rsp}")
    detectors = detector_rsp.get('DetectorIds', [])
    print(detectors)
    found = False
    found_scan = {}
    for detector in detectors:
        print(f"detector_id: {detector}")
        try:
            describe_rsp = client_guard.describe_malware_scans(DetectorId=detector)
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to run describe scan {error}"
            return {"status": 403, "msg": error_msg, "inputs": inputs}
        print(f"detector rsp {describe_rsp}")
        scans = describe_rsp.get('Scans', [])
        for scan in scans:
            print(f"scan {scan}")
            if scan.get('ScanId', None) == scan_id:
                found = True
                found_scan = scan
                scan_status = scan.get('ScanStatus', None)
                print(f"scan status: {scan_status}")
    if not found:
        inputs = {
            'scan_id': scan_id,
            'instance_id': instance_id,
            'scan_results': None
        }
        return {"status": 404, "msg": "scan not found", "inputs": inputs}
    if scan_status == 'RUNNING':
        inputs = {
            'scan_id': scan_id,
            'instance_id': instance_id,
            'scan_results': None
        }
        return {"status": 205, "msg": "running", "inputs": inputs}
    elif scan_status == 'COMPLETED':
        scan_results = found_scan.get('ScanResultDetails', {}).get('ScanResult', None)
        inputs = {
            'scan_id': scan_id,
            'instance_id': instance_id,
            'scan_results': scan_results
        }
        return {"status": 200, "msg": "completed",
            "inputs": inputs}
    else:
        inputs = {
            'scan_id': scan_id,
            'instance_id': instance_id,
            'scan_results': None
        }
        return {"status": 405, "msg": "scan did not complete","inputs": inputs}