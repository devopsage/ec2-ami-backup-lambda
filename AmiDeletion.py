#==============================================================================
# script to remove the older ami backup based on the retention period defined
# Owner: DevOpsAGE Technologies
# Contact: devopsage@gmail.com
# note: make sure to change the region name below in the script
# Disclaimer: This Script does not comes with any guaranty, please go through it carefully before executing it. DevOpsAGE Will 
# not be responsible for any loss of data or any Issues happened
#==============================================================================

import boto3
import datetime
import os
import time

accountNumber = os.environ['AWS_ACCOUNT_NUMBER']

ec = boto3.client('ec2', 'ap-southeast-1')

def lambda_handler(event, context):

    imagesResponse = ec.describe_images(
        DryRun=False,
        Owners=[accountNumber],
        Filters=[
            {'Name': 'tag:Backup', 'Values': ['True']}
        ]
    ).get(
        'Images', []
    )

    amiList = []
    currentDate = datetime.datetime.now().strftime('%m-%d-%Y-%H:%M:%S')
    time.sleep(5)
    for image in imagesResponse:
        deleteOn = ''
        for tag in image['Tags']:
            if tag['Key'] == 'DeleteOn':
                deleteOn = tag['Value']
                break
        if deleteOn == '':
            continue
        if deleteOn <= currentDate:
            print "\nCleaning up AMI %s" % (image['ImageId'])
            ec.deregister_image(
                DryRun=False,
                ImageId=image['ImageId']
            )
            amiList.append(image['ImageId'])
            snapshots = ec.describe_snapshots(
                DryRun=False,
                OwnerIds=[
                    accountNumber
                ],
                Filters=[
                    {
                        'Name': 'description',
                        'Values': [
                            '*'+image['ImageId']+'*'
                        ]
                    }
                ]
            ).get(
                'Snapshots', []
            )
            for snapshot in snapshots:
                print ">>Cleaning up Snapshot %s" % (snapshot['SnapshotId'])
                time.sleep(5)
                ec.delete_snapshot(
                    DryRun = False,
                    SnapshotId = snapshot['SnapshotId']
                )
        else:
            print "\n%s not yet scheduled for cleanup" % (image['ImageId'])
    if len(amiList)==0:
        print "\n\nNo AMIs were deleted"
    else:
        print "\n\n%d AMIs were deleted\nDeleted the following:" %(len(amiList))
        for ami in amiList:
            print ami
