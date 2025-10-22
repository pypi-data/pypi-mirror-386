# Copyright (c) 2016, 2023, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at https://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# coding: utf-8
# Copyright (c) 2016, 2021, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.
from services.resource_analytics.src.oci_cli_resource_analytics.generated import resource_analytics_service_cli
from services.resource_analytics.src.oci_cli_tenancy_attachment.generated import tenancyattachment_cli

# Remove collection group
# oci resource-analytics tenancy-attachment tenancy-attachment-collection
tenancyattachment_cli.tenancy_attachment_root_group.commands.pop(tenancyattachment_cli.tenancy_attachment_collection_group.name)
# Add list command from collection to root group
# oci resource-analytics tenancy-attachment list
tenancyattachment_cli.tenancy_attachment_group.add_command(tenancyattachment_cli.list_tenancy_attachments)

# Rearrange nested groups to be "top" level
# oci resource-analytics tenancy-attachment tenancy-attachment <command>
tenancyattachment_cli.tenancy_attachment_root_group.commands.pop(tenancyattachment_cli.tenancy_attachment_group.name)
# -> oci resource-analytics tenancy-attachment <command>
resource_analytics_service_cli.resource_analytics_service_group.add_command(tenancyattachment_cli.tenancy_attachment_group)
