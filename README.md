# Spark Structured Streaming Demo with EMR ON MSK

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
    - The cluster has 1 master and 1 core nodes running on r5.xlarge.
    - The cluster is configured to run one Spark job at a time.
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
Install the folowing tools:
1. [Python 3.6 +](https://www.python.org/downloads/).
2. [Node.js 10.3.0 +](https://nodejs.org/en/)
3. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html#install-macosos-bundled). Configure the CLI by `aws configure`.
4. [CDK toolkit](https://cdkworkshop.com/15-prerequisites/500-toolkit.html)
5. [One-off CDK bootstrap](https://cdkworkshop.com/20-typescript/20-create-project/500-deploy.html) for the first time deployment.

#### Deploy
```bash
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt

cdk deploy
```

## Post-deployment

1. Open the "Kafka Client" IDE in Cloud9 console. Create one if the Cloud9 IDE doesn't exist. 
```
VPC prefix: 'emr-stream-demo'
Instance Type: 't3.small'
```
2. [Attach the IAM role that contains `Cloud9Admin` to your IDE](https://www.eksworkshop.com/020_prerequisites/ec2instance/). 
3. [Turn off AWS managed temporary credentials](https://www.eksworkshop.com/020_prerequisites/workspaceiam/)
4. Run the script to configure the cloud9 IDE environment:
```bash
curl https://raw.githubusercontent.com/melodyyangaws/emr-stream-demo/master/deployment/app_code/post-deployment.sh | bash
```
5. Launching a new termnial window in Cloud9, send the sample data to MSK:
```bash
curl -s https://raw.githubusercontent.com/melodyyangaws/emr-stream-demo/master/deployment/app_code/data/nycTaxiRides.gz | zcat | split -l 10000 --filter="kafka_2.12-2.2.1/bin/kafka-console-producer.sh --broker-list ${MSK_SERVER} --topic taxirides ; sleep 0.2"  > /dev/null
```
6. Launching the 3rd termnial window and monitor the source MSK topic:
```bash
kafka_2.12-2.2.1/bin/kafka-console-consumer.sh --bootstrap-server ${MSK_SERVER} --topic taxirides --from-beginning
```


## Submit job with EMR on EKS
```bash
aws emr-containers start-job-run \
--virtual-cluster-id $VIRTUAL_CLUSTER_ID \
--name msk_consumer \
--execution-role-arn $EMR_ROLE_ARN \
--release-label emr-5.33.0-latest \
--job-driver '{
    "sparkSubmitJobDriver":{
        "entryPoint": "s3://'$S3BUCKET'/app_code/job/msk_consumer.py","entryPointArguments":["'$MSK_SERVER'","s3://'$S3BUCKET'/stream/checkpoint/emreks","emreks_output"],"sparkSubmitParameters": "--conf spark.jars.ivy=/tmp/ivy --conf spark.jars.packages=org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.7 --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.7 --conf spark.cleaner.referenceTracking.cleanCheckpoints=true --conf spark.executor.instances=2 --conf spark.executor.memory=2G --conf spark.driver.memory=1G --conf spark.executor.cores=2"}
    }'

# Verify the job is running in EKS
kubectl get po -n emr

# verify in EMR console
# in Cloud9, run the consumer tool to check if any data comeing through in the target Kafka topic
kafka_2.12-2.2.1/bin/kafka-console-consumer.sh --bootstrap-server ${MSK_SERVER} --topic emreks_output --from-beginning
```
## OPTIONAL: EMR on EKS with Fargate
```bash
aws emr-containers start-job-run \
--virtual-cluster-id $SERVERLESS_VIRTUAL_CLUSTER_ID \
--name msk_consumer \
--execution-role-arn $EMR_ROLE_ARN \
--release-label emr-5.33.0-latest \
--job-driver '{
    "sparkSubmitJobDriver":{
        "entryPoint": "s3://'$S3BUCKET'/app_code/job/msk_consumer.py","entryPointArguments":["'$MSK_SERVER'","s3://'$S3BUCKET'/stream/checkpoint/emreksfg","emreksfg_output"],"sparkSubmitParameters": "--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.7 --conf spark.cleaner.referenceTracking.cleanCheckpoints=true --conf spark.executor.instances=2 --conf spark.executor.memory=2G --conf spark.driver.memory=1G --conf spark.executor.cores=2"}
    }'

# Verify the job is running in EKS Fargate
kubectl get po -n emrserverless

# verify in EMR console
# in Cloud9, run the consumer tool to check if any data comeing through in the target Kafka topic
kafka_2.12-2.2.1/bin/kafka-console-consumer.sh --bootstrap-server ${MSK_SERVER} --topic emreksfg_output --from-beginning
```

## OPTIONAL: Submit EMR step

```bash
cluster_id=$(aws emr list-clusters --cluster-states WAITING --query 'Clusters[?Name==`emr-stream-demo`].Id' --output text)
aws emr add-steps \
--cluster-id $cluster_id \
--steps Type=spark,Name=emrec2_stream,Args=[--deploy-mode,cluster,--conf,spark.cleaner.referenceTracking.cleanCheckpoints=true,--conf,spark.executor.instances=2,--conf,spark.executor.memory=2G,--conf,spark.driver.memory=2G,--conf,spark.executor.cores=2,--packages,org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1,s3://$S3BUCKET/app_code/job/msk_consumer.py,"$MSK_SERVER",s3://$S3BUCKET/stream/checkpoint/emrec2,emrec2_output],ActionOnFailure=CONTINUE  


# verify in EMR console
# in Cloud9, run the consumer tool to check if any data comeing through in the target Kafka topic
```bash
kafka_2.12-2.2.1/bin/kafka-console-consumer.sh --bootstrap-server ${MSK_SERVER} --topic emrec2_output --from-beginning
```


## Useful commands

 * `kubectl get pod -n emr`               list running Spark jobs
 * `kubectl delete pod --all -n emr`      delete all Spark jobs
 * `kubectl logs <pod name> -n emr`       check logs against a pod in the emr namespace
 * `kubectl get node --label-columns=eks.amazonaws.com/capacityType,topology.kubernetes.io/zone` check EKS compute capacity types and AZ distribution.


## Clean up
Run the clean-up script with:
```bash
curl https://raw.githubusercontent.com/melodyyangaws/emr-stream-demo/master/deployment/app_code/delete_all.sh | bash
```
Go to the [CloudFormation console](https://console.aws.amazon.com/cloudformation/home?region=us-east-1), manually delete the remaining resources if needed.
