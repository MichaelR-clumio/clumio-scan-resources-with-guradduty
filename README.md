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

# FOR EXAMPLE PURPOSES ONLY

#
# Requirements: 
#  Secure account to deploy resources for scanning 
#  Local account to install lambdas and step function
#  Role is secure account that can descibe and delete EC2 scanned resources and initiate guardduty scans
#  Role in local account that can assume role in secure account
#  
#  S3 bucket in same region where stepfunction/lambdas are to be deployed 
#
# Upload lambda zip file "clumio_scan_restore_guardduty.zip" into S3 bucket
# Modify the lambda deployment cft "clumio_restore_and_scan_guardduty_lambda_deploy_cft.yaml" to include your S3 bucket name and modify key name to include prefix if lambda zip is not in root of the bucket
# Run the lambda deployment CFT
# Modify step function json "clumio_restore_and_scan_state_machine.json" to point to your lambda functions (6 in total).  Note:  name will be the same but aws account id an region will be different.
# Create a new step function.  select on the code option in the builder.  copy and paste code from your modified step function json file.
#
# Modify inputs json "example_step_function_inputs.json" to include your data
#  - "source_account": "111222333444",  account where data was backed up from
#  - "source_region": "us-east-2",      region where data was backed up from
#   NEXT Two values during which backups (by time) you want to use
#  - "search_day_offset": 0,  - Point in time to use a reference for the search.  0 means start with most recent backups, 1 means start with backup from 1 day ago, etc      
#  - "search_direction": "before",  - direction to search.  before or after - before searches for dates at or older then the point of refence.  after searches for dates newer then the point of reference

# Target values are configuraiton or infrastuructor values in the secure account

#  - "target_account": "555666777888",
#  "target_region": "us-east-1",
#  "target_az": "us-east-1a",
#  "target_iam_instance_profile_name": "",
#  "target_key_pair_name": "zxxz-323724565630-ec2-key",
#  "target_security_group_native_ids": [    "sg-0546facc66de14dd3 ],
#  "target_subnet_native_id": "subnet-0340ef13d020c1ee1",
#  "target_vpc_native_id": "vpc-0a4cde925ca123ff2",
#  "target_kms_key_native_id": "",
#  "target_role_arn": "arn:aws:iam::555666777888:role/<local iam role that can assume ou role>",

# Execute the step function passing it the contents of the modified inputs json.

# Lambda function code

# aws_guardduty_check_scan_status.py
# aws_guardduty_scan_response.py
# aws_guardduty_start_scan.py
# clumio_ec2_list_backups.py
# clumio_ec2_restore_guardduty.py
# clumio_retrieve_task.py

# clumio_sdk_v8c.py - this is the "helper" sdk
