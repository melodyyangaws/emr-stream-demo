FROM 895885662937.dkr.ecr.us-west-2.amazonaws.com/spark/emr-6.5.0:latest
USER root
RUN pip3 install --upgrade boto3 pandas numpy
USER hadoop:hadoop