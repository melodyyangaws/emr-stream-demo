######################################################################################################################
# Copyright 2020-2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                      #
#                                                                                                                   #
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance    #
# with the License. A copy of the License is located at                                                             #
#                                                                                                                   #
#     http://www.apache.org/licenses/LICENSE-2.0                                                                    #
#                                                                                                                   #
# or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES #
# OR CONDITIONS OF ANY KIND, express o#implied. See the License for the specific language governing permissions     #
# and limitations under the License.  																				#                                                                              #
######################################################################################################################

import typing

from aws_cdk import (
    core,
    aws_iam as iam
)

class IamConst(core.Construct):

    @property
    def managed_node_role(self):
        return self._managed_node_role

    @property
    def admin_role(self):
        return self._clusterAdminRole
        
    @property
    def emr_svc_role(self):
        return self._emrsvcrole 

    def __init__(self,scope: core.Construct, id:str, cluster_name:str, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

        # EKS admin role
        self._clusterAdminRole = iam.Role(self, 'ClusterAdmin',
            assumed_by= iam.AccountRootPrincipal()
        )
        self._clusterAdminRole.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=[
                "eks:Describe*",
                "eks:List*",
                "eks:AccessKubernetesApi",
                "ssm:GetParameter",
                "iam:ListRoles"
            ],
        ))
        core.Tags.of(self._clusterAdminRole).add(
            key='eks/%s/type' % cluster_name, 
            value='admin-role'
        )

        # Managed Node Group Instance Role
        _managed_node_managed_policies = (
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEKSWorkerNodePolicy'),
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEKS_CNI_Policy'),
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEC2ContainerRegistryReadOnly'),
            iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchAgentServerPolicy'), 
        )
        self._managed_node_role = iam.Role(self,'NodeInstance-Role',
            path='/',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=list(_managed_node_managed_policies),
        )
        # EMR container service role
        self._emrsvcrole = iam.Role.from_role_arn(self, "EmrSvcRole", 
            role_arn=f"arn:aws:iam::{core.Aws.ACCOUNT_ID}:role/AWSServiceRoleForAmazonEMRContainers", 
            mutable=False
        )

        # Cloud9 EC2 role
        self._cloud9_role=iam.Role(self,"Cloud9Admin",
            path='/',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess')]
        )
        self._cloud9_role.add_to_policy(iam.PolicyStatement(
            resources=[self._clusterAdminRole.role_arn],
            actions=["sts:AssumeRole"]
        ))
        self._cloud9_role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["eks:Describe*","ssm:GetParameter","kafka:DescribeCluster","kafka:UpdateClusterConfiguration"]
        ))
        self._cloud9_role.add_to_policy(iam.PolicyStatement(
            resources=[f"arn:aws:kafka:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:/v1/clusters"],
            actions=["kafka:ListClusters"]
        ))
        self._cloud9_role.add_to_policy(iam.PolicyStatement(
            resources=[f"arn:aws:kafka:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:/v1/configurations"],
            actions=["kafka:CreateConfiguration"]
        ))