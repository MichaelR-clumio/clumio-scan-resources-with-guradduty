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
from clumio_sdk_v9 import DynamoDBBackupList, RestoreDDN, ClumioConnectAccount, AWSOrgAccount, ListEC2Instance, \
    EnvironmentId, RestoreEC2, EC2BackupList, EBSBackupList, RestoreEBS, OnDemandBackupEC2, RetrieveTask


def lambda_handler(events, context):
    bear = events.get('bear', None)
    source_account = events.get('source_account', None)
    source_region = events.get('source_region', None)
    search_direction = events.get('search_direction', None)
    search_day_offset_input = events.get('search_day_offset', None)
    debug_input = events.get('debug', None)

    # Validate inputs
    try:
        search_day_offset = int(search_day_offset_input)
    except ValueError as e:
        error = f"invalid task id: {e}"
        return {"status": 401, "records": [], "msg": f"failed {error}"}
    try:
        debug = int(debug_input)
    except ValueError as e:
        error = f"invalid debug: {e}"
        return {"status": 402, "records": [],"msg": f"failed {error}"}

    # Initiate API and configure
    ec2_backup_list_api = EC2BackupList()
    ec2_backup_list_api.set_token(bear)
    ec2_backup_list_api.set_debug(debug)

    # Set search parameters
    ec2_backup_list_api.set_search_start_day(search_day_offset)
    ec2_backup_list_api.set_search_time_frame_before_after(search_direction)
    ec2_backup_list_api.set_aws_account_id(source_account)
    ec2_backup_list_api.set_aws_region(source_region)

    # Run search
    ec2_backup_list_api.run_all()

    # Parse and return results
    result_dict = ec2_backup_list_api.ec2_parse_results("restore")
    ec2_backup_records = result_dict.get("records", [])
    if len(ec2_backup_records) == 0:
        return {"status": 207, "records": [],"msg": "empty set"}
    else:
        return {"status": 200, "records": ec2_backup_records, "msg": "completed"}