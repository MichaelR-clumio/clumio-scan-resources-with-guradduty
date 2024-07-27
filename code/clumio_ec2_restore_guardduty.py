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

from botocore.exceptions import ClientError
import random
import string
from clumio_sdk_v9 import DynamoDBBackupList, RestoreDDN, ClumioConnectAccount, AWSOrgAccount, ListEC2Instance, \
    EnvironmentId, RestoreEC2, EC2BackupList, EBSBackupList, RestoreEBS, OnDemandBackupEC2, RetrieveTask


def lambda_handler(events, context):
    record = events.get("record", {})
    bear = events.get('bear', None)
    target_account = events.get('target_account', None)
    target_region = events.get('target_region', None)
    debug_input = events.get('debug', None)
    target_az = events.get("target_az", None)
    target_iam_instance_profile_name = events.get("target_iam_instance_profile_name", None)
    target_key_pair_name = events.get("target_key_pair_name", None)
    target_security_group_native_ids = events.get("target_security_group_native_ids", None)
    target_subnet_native_id = events.get("target_subnet_native_id", None)
    target_vpc_native_id = events.get("target_vpc_native_id", None)
    target_kms_key_native_id = events.get("target_kms_key_native_id", None)

    inputs = {
        'run_token': None,
        'task': None
    }

    # Validate inputs
    try:
        debug = int(debug_input)
    except ValueError as e:
        error = f"invalid debug: {e}"
        return {"status": 401, "task": None,"msg": f"failed {error}",
                "inputs": inputs}

    if len(record) == 0:
        return {"status": 205, "msg": "no records",
                "inputs": inputs}

    # Initiate API and configure
    ec2_restore_api = RestoreEC2()
    ec2_restore_api.set_token(bear)
    ec2_restore_api.set_debug(debug)
    run_token = ''.join(random.choices(string.ascii_letters, k=13))

    if record:
        source_backup_id = record.get("backup_record", {}).get('source_backup_id', None)
        source_instance_id = record.get("instance_id")
    else:
        error = f"invalid backup record {record}"
        return {"status": 402, "msg": f"failed {error}",
                "inputs": inputs}
    new_tag_identifier = [
        {"key": "InstanceToScanStatus", "value": "enable"},
        {"key": "OrginalInstanceId", "value": source_instance_id},
        {"key": "OriginalBackupId", "value": source_backup_id},
        {"key": "ClumioTaskToken", "value": run_token}
    ]
    ec2_restore_api.add_ec2_tag_to_instance(new_tag_identifier)
    # Set restore target information

    target = {
        "account": target_account,
        "region": target_region,
        "aws_az": target_az,
        "iam_instance_profile_name": target_iam_instance_profile_name,
        "key_pair_name": target_key_pair_name,
        "security_group_native_ids": target_security_group_native_ids,
        "subnet_native_id": target_subnet_native_id,
        "vpc_native_id": target_vpc_native_id,
        "kms_key_native_id": target_kms_key_native_id
    }
    result_target = ec2_restore_api.set_target_for_instance_restore(target)
    print(f"target set status {result_target}")
    # Run restore
    ec2_restore_api.save_restore_task()
    result_run = ec2_restore_api.ec2_restore_from_record([record])
    print(result_run)

    if result_run:
        # Get a list of tasks for all of the restores.
        task_list = ec2_restore_api.get_restore_task_list()
        if debug > 5: print(task_list)
        task = task_list[0].get("task",None)
        inputs = {
            'run_token': run_token,
            'task': task
        }
        if len(task_list) > 0:
            return {"status": 200, "msg": "completed",
                    "inputs": inputs}
        else:
            return {"status": 207, "msg": "no restores",
                    "inputs": inputs}
    else:
        return {"status": 403, "msg": "failed",
                "inputs": inputs}