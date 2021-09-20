#!/bin/bash

export stack_name="${1:-EMROnEKS}"

# delete the rest from CF
echo "Delete the rest of resources by CloudFormation delete command"
aws cloudformation delete-stack --stack-name $stack_name