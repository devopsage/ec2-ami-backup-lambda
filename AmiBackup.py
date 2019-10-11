#==================================================================
## Script to take the AMI backup of an ec2 instance based on tag
## owner: DevOpsAGE Technologies
## Contact: devopsage@gmail.com
# AMI taken with Noreboot=True
# Disclaimer: This Script does not comes with any guaranty, please go through it carefully before executing it. DevOpsAGE Will 
# not be responsible for any loss of data or any Issues happened
#==================================================================

import boto3
import collections
import datetime
import os
import time

ec = boto3.client('ec2')

# Main handler function
def lambda_handler(event, context):

  accountNumber = os.environ['AWS_ACCOUNT_ID']
  retentionDays = int(os.environ['RETENTION_DAYS'])
  
  # Retriving all EC2 instances
  reservations = ec.describe_instances(
    Filters=[
      {'Name': 'tag:Backup', 'Values': ['True']}
    ]
  ).get(
    'Reservations', []
  )

  instances = sum(
    [
      [i for i in r['Instances']]
      for r in reservations
    ], [])

  print "Found %d instances that need backing up" % len(instances)

  #to_tag = collections.defaultdict(list)
  amiList = []
  # For each instance if they have Retention Tag, get the number of days from Instance tag else from lambda parameter
  for instance in instances:
    try:
      retention_days = [
        int(t.get('Value')) for t in instance['Tags']
        if t['Key'] == 'Retention'][0]
    except IndexError:
      retention_days = retentionDays

      create_time = datetime.datetime.now()
      create_fmt = create_time.strftime('%m-%d-%Y-%H-%M-%S')

      for tag in instance['Tags']:
        if tag['Key'] == 'Name':
          amiName = tag['Value']
          break

      nametag = amiName + "-" + "Lambda" + "-" + instance['InstanceId'] + "-" + create_fmt

      AMIid = ec.create_image(InstanceId=instance['InstanceId'], Name= nametag, Description="Lambda created AMI of instance " + instance['InstanceId'] + " on " + create_fmt, NoReboot=True, DryRun=False)

      delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
      delete_fmt = delete_date.strftime('%m-%d-%Y')
      print "Will delete %s AMIs on %s" % (AMIid['ImageId'], delete_fmt)

      ec.create_tags(
        Resources=[AMIid['ImageId']],
        Tags=[
          {'Key': 'DeleteOn', 'Value': delete_fmt},
          {'Key': 'Backup', 'Value': 'True'},
          {'Key': 'Name', 'Value': nametag}
        ]
      )

      # to_tag[retention_days].append(AMIid['ImageId'])

      amiList.append(AMIid['ImageId'])
      print "Retaining AMI %s of instance %s for %d days" % (
        AMIid['ImageId'],
        instance['InstanceId'],
        retention_days,
      )

  snapshotMaster = []
  time.sleep(10)
  print amiList
  for ami in amiList:
    print ami
    snapshots = ec.describe_snapshots(
      DryRun=False,
      OwnerIds=[
        accountNumber
      ],
      Filters=[{
        'Name': 'description',
        'Values': [
          '*'+ami+'*'
        ]
      }]
    ).get(
      'Snapshots', []
    )
    print "****************"
    delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
    delete_fmt = delete_date.strftime('%m-%d-%Y')
    snapnametag = ami + "-" + "Lambda-created"

    for snapshot in snapshots:
      print snapshot['SnapshotId']
      ec.create_tags(
        Resources=[snapshot['SnapshotId']],
        Tags=[
          {'Key': 'DeleteOn', 'Value': delete_fmt},
          {'Key': 'Backup', 'Value': 'True'},
          {'Key': 'Name', 'Value': snapnametag},
        ]
      )
