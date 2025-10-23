# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutron.objects.plugins.ml2 import geneveallocation
from neutron.tests.functional.objects.plugins.ml2 import test_base


class TestGeneveSegmentAllocationMySQL(test_base._SegmentAllocationMySQL):
    segment_allocation_class = geneveallocation.GeneveAllocation


class TestGeneveSegmentAllocationPostgreSQL(
        test_base._SegmentAllocationPostgreSQL):
    segment_allocation_class = geneveallocation.GeneveAllocation
