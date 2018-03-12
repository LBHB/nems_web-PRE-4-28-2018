import boto3

# Start ec2 connection
ec2 = boto3.connect_ec2()


# Create new instances/machines
# TODO: Where does the image id come from? how can one be generated?
ec2.create_instances(ImageId='<ami-image-id>', MinCount=1, MaxCount=5)


# Stop then terminate instances from a list
ids = ['id1', 'id2', 'id3']
ec2.instances.filter(InstanceIds=ids).stop()
ec2.instances.filter(InstanceIds=ids).terminate()


# Check what instances are currently running
instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
for instance in instances:
    print(instance.id, instance.instance_type)
run_count = len(instances)

# Use this to determine if new instances should be added?
# When would this be checked? Each time a new job is added?
JOBS_PER_INSTANCE = 10
#query tQueue to get number of queued jobs
num_jobs = 10
if num_jobs / run_count > JOBS_PER_INSTANCE:
    ec2.create_instances(ImageId='<ami-image-id>', MinCount=1, MaxCount=5)
    
# same for reducing intances?
if num_jobs / run_count-1 < JOBS_PER_INSTANCE:
    # Again, where to get these ids from?
    # For running ones, id would be stored in cell db?
    ec2.instances.filter(InstanceIds=ids).stop()
    ec2.instances.filter(InstanceIds=ids).terminate()
    
    
# file management / S3

#establish s3 connection
s3 = boto3.resource('s3')

#create new storage bucket
s3.create_bucket(Butcket='Bucket_Name')

# get bucket reference
bucket = s3.bucket('Bucket_Name')

# change access type of bucket
bucket.Acl().put(ACL='public-read')

# store file or file object (open as binary)
s3.Object('mybucket', 'hello.txt').put(Body=open('/tmp/hello.txt', 'rb'))

# download 
bucket.download_file('file_name_in_s3.png', 'file_name_to_store_locally.png')
