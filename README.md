# Spark Structured Streaming Demo with MSK and EMR

This is a project developed in Python [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html).
It include sample data, Kafka producer simulator and a consumer example that can be run with EMR on EC2 or EMR on EKS. 

The infrastructure deployment includes the following:
- A new S3 bucket to store sample data and stream job code
- An EKS cluster in a new VPC across 2 AZs
    - The Cluster has 2 default managed node groups: the OnDemand nodegroup scales from 1 to 5, SPOT instance nodegroup can scale from 1 to 30. 
    - It also has a Fargate profile set to use the `emrserverless` namespace
- Two EMR virtual clusters in the same VPC
    - The first virtual cluster uses the `emr` namespace on managed node groups
    - The second virtual cluster uses the `emrserverless` namespace on a Fargate profile
    - All EMR on EKS configuration is done, including a cluster role bound to an IAM role
- A MSK Cluster in the same VPC with 2 brokers in total. Kafka version is 2.6.1.
    - A Cloud9 IDE as the command line environment in the demo. 
    - Kafka Client tool will be installed on the Cloud9 IDE
- Optionally, sets up an EMR on EC2 cluster with managed scaling enabled.
    - The cluster has 1 master and 1 core nodes running on Graviton2 (r6g.xlarge).
    - The cluster is configured for running one Spark job at a time.
    - The EMR cluster can scale from 1 to 10 core + task nodes

## Deploy Infrastructure

The provisioning takes about 30 minutes to complete. 
Two ways to deploy:
1. AWS CloudFormation template (CFN) 
2. [AWS Cloud Development Kit (AWS CDK)](https://docs.aws.amazon.com/cdk/latest/guide/home.html).

### CloudFormation Deployment

  |   Region  |   Launch Template |
  |  ---------------------------   |   -----------------------  |
  |  ---------------------------   |   -----------------------  |
  **US East (N. Virginia)**| [![Deploy to AWS](source/app_resources/00-deploy-to-aws.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?stackName=StreamOnEKS&templateURL=https://blogpost-sparkoneks-us-east-1.s3.amazonaws.com/emr-stream-demo/v1.0.0/StreamOnEKS.template) 

* To launch in a different AWS Region, check out the following customization section, or use the CDK deployment option.

### Customization
You can customize the solution, such as remove the nested stack of EMR cluster setup, then generate the CFN tmeplates in your region: 
```bash
export BUCKET_NAME_PREFIX=<my-bucket-name> # bucket where customized code will reside
export AWS_REGION=<your-region>
export SOLUTION_NAME=emr-stream-demo
export VERSION=v1.0.0 # version number for the customized code

./deployment/build-s3-dist.sh $BUCKET_NAME_PREFIX $SOLUTION_NAME $VERSION

# create the bucket where customized code will reside
aws s3 mb s3://$BUCKET_NAME_PREFIX-$AWS_REGION --region $AWS_REGION

# Upload deployment assets to the S3 bucket
aws s3 cp ./deployment/global-s3-assets/ s3://$BUCKET_NAME_PREFIX-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control
aws s3 cp ./deployment/regional-s3-assets/ s3://$BUCKET_NAME_PREFIX-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control

echo -e "\nIn web browser, paste the URL to launch the template: https://console.aws.amazon.com/cloudformation/home?region=$AWS_REGION#/stacks/quickcreate?stackName=StreamOnEKS&templateURL=https://$BUCKET_NAME_PREFIX-$AWS_REGION.s3.amazonaws.com/$SOLUTION_NAME/$VERSION/StreamOnEKS.template\n"
```

### CDK Deployment

#### Prerequisites 
1. [Python 3.6 or later](https://www.python.org/downloads/).
2. [Node.js 10.3.0 or later](https://nodejs.org/en/)
3. [AWS CLI for windows](https://docs.aws.amazon.com/cli/latest/userguide/install-windows.html#install-msi-on-windows) or [for the rest of OS](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html#install-macosos-bundled). Configure the CLI by `aws configure`.
4. [CDK toolkit](https://cdkworkshop.com/15-prerequisites/500-toolkit.html)
5. [One-off CDK bootstrap](https://cdkworkshop.com/20-typescript/20-create-project/500-deploy.html) for the first time deployment.

See the `troubleshooting` section, if you have a problem in the CDK deployment.

#### Deploy
```bash
python3 -m venv .env
```
For Windows, activate the virtualenv by `% .env\Scripts\activate.bat`.
For other OS, run the followings:
```bash
source .env/bin/activate
pip install -e source

cd source
cdk deploy
```
To remove the deployment from your account:
```bash
cd source
cdk destroy
```
#### Troubleshooting

1. If you see the issue `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)`, most likely it means no default certificate authority for your Python installation on OSX. Refer to the [answer](https://stackoverflow.com/questions/52805115/0nd) installing `Install Certificates.command` should fix your local environment. Otherwise, use [Cloud9](https://aws.amazon.com/cloud9/details/) to deploy the CDK instead.

2. If an error appears during the CDK deployment: `Failed to create resource. IAM role’s policy must include the "ec2:DescribeVpcs" action`. The possible causes are: 1) you have reach the quota limits of Amazon VPC resources per Region in your AWS account. Please deploy to a different region or a different account. 2) based on this [CDK issue](https://github.com/aws/aws-cdk/issues/9027), you can retry without any changes, it will work. 3) If you are in a branch new AWS account, manually delete the AWSServiceRoleForAmazonEKS from IAM role console before the deployment. 

## Post-deployment

1. Go to "Kafka Client" IDE in Cloud9 console, configure environment:
```bash
curl https://raw.githubusercontent.com/melodyyangaws/emr-stream-demo/master/deployment/app_code/post-deployment.sh | bash
```
3. Launching a new termnial window in Cloud9, send data to MSK:
```bash
curl -s https://${S3BUCKET}.s3.${AWS_REGION}.amazonaws.com/app_code/data/nycTaxiRides.gz | zcat | split -l 10000 --filter="kafka_2.12-2.2.1/bin/kafka-console-producer.sh --broker-list ${MSK_SERVER} --topic taxirides; sleep 0.2" > /dev/null
```
4. Launching the 3rd termnial window and monitor the source MSK queue:
```bash
kafka_2.12-2.2.1/bin/kafka-console-consumer.sh --bootstrap-server ${MSK_SERVER} --topic taxirides --from-beginning
```
5. Launching the 4th termnial window and monitor the target MSK queue:
```bash
kafka_2.12-2.2.1/bin/kafka-console-consumer.sh --bootstrap-server ${MSK_SERVER} --topic taxirides_output --from-beginning
```

## Submit job with EMR on EKS

## OPTIONAL: Submit EMR step



[*^ back to top*](#Table-of-Contents)
## Useful commands

 * `kubectl get pod -n emr`               list running Spark jobs
 * `kubectl delete pod --all -n emr`      delete all Spark jobs
 * `kubectl logs <pod name> -n emr`       check logs against a pod in the emr namespace
 * `kubectl get node --label-columns=eks.amazonaws.com/capacityType,topology.kubernetes.io/zone` check EKS compute capacity types and AZ distribution.

[*^ back to top*](#Table-of-Contents)
## Clean up
Run the clean-up script with your CloudFormation stack name EMROnEKS. If you see the error "(ResourceInUse) when calling the DeleteTargetGroup operation", simply run the script again.
```bash
cd emr-stream-demo
./deployment/delete_all.sh
```
Go to the [CloudFormation console](https://console.aws.amazon.com/cloudformation/home?region=us-east-1), manually delete the remaining resources if needed.
