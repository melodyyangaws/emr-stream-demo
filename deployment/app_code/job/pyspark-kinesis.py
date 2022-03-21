from pyspark.streaming.kinesis import KinesisUtils, InitialPositionInStream
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql.types import StructField, StructType, StringType, IntegerType
import boto3,json,sys

# def printRecord(rdd):
#     print("========================================================")
#     print("Starting new RDD")
#     print("========================================================")
#     rdd.foreach(lambda record: print(record.encode('utf8')))

if __name__ == "__main__":

    # creating the Kinesis stream
    stream_name='pyspark-kinesis'
    client_region = sys.argv[1]
    client = boto3.client('kinesis', client_region)
    try:
        print("create a new stream")
        client.create_stream(
                StreamName=stream_name,
                ShardCount=1)
    except:
        print("the stream exists")
    # creating a couple of messages to send to kinesis
    messages = [
        {'message_type': 'message1', 'count': 2},
        {'message_type': 'message2', 'count': 1},
        {'message_type': 'message1', 'count': 2},
        {'message_type': 'message3', 'count': 3},
        {'message_type': 'message1', 'count': 5}
    ]

    for message in messages:
        client.put_record(
            StreamName=stream_name,
            Data=json.dumps(message),
            PartitionKey='part_key')
 

    # start Spark process, read from kinesis
    sc = SparkContext(appName="PythonStreamingKinesisAsl")
    ssc = StreamingContext(sc, 5)
    kinesis = KinesisUtils.createStream(ssc, stream_name,stream_name, 'https://kinesis.'+client_region+'.amazonaws.com',client_region, InitialPositionInStream.TRIM_HORIZON, 2)
    kinesis.pprint()
    # write to s3
    py_rdd = kinesis.map(lambda x: json.loads(x.encode('utf8')))
    py_rdd.saveAsTextFiles(sys.argv[2])

    # def format_sample(x):
    #     data = json.loads(x)
    #     return (data['message_type'], json.dumps(data))
    ## print to console
    # parsed = kinesis.map(lambda x: format_sample(x.encode('utf8')))
    # parsed.pprint()

    ssc.start()
    ssc.awaitTermination()