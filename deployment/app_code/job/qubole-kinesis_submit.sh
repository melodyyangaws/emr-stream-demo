export AWS_REGION=$(aws configure list | grep region | awk '{print $2}')
export ACCOUNT_ID=$(aws sts get-caller-identity --output text --query Account)
export ECR_URL=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

aws emr-containers start-job-run \
--virtual-cluster-id $VIRTUAL_CLUSTER_ID \
--name kinesis-demo \
--execution-role-arn $EMR_ROLE_ARN \
--release-label emr-6.2.0-latest \
--job-driver '{
    "sparkSubmitJobDriver":{
        "entryPoint": "s3://'$S3BUCKET'/app_code/job/qubole-kinesis.py",
        "entryPointArguments":["'${AWS_REGION}'","s3://'${S3BUCKET}'/qubolecheckpoint","s3://'${S3BUCKET}'/qubole-kinesis-output"],
        "sparkSubmitParameters": "--jars https://repo1.maven.org/maven2/com/qubole/spark/spark-sql-kinesis_2.12/1.2.0_spark-3.0/spark-sql-kinesis_2.12-1.2.0_spark-3.0.jar,https://repo1.maven.org/maven2/com/amazonaws/amazon-kinesis-client/1.14.8/amazon-kinesis-client-1.14.8.jar,https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-kinesis/1.12.31/aws-java-sdk-kinesis-1.12.31.jar --conf spark.cleaner.referenceTracking.cleanCheckpoints=true"}}' \
--configuration-overrides '{
    "applicationConfiguration": [
        {
            "classification": "spark-defaults",
            "properties": {
                "spark.kubernetes.container.image": "'${ECR_URL}'/emr6.5_custom_boto3:latest"
            }
        }
    ],
    "monitoringConfiguration": {
        "s3MonitoringConfiguration": {"logUri": "s3://'${S3BUCKET}'/elasticmapreduce/kinesis-fargate-log/"}
    }
}'        
