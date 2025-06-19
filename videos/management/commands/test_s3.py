from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.exceptions import ClientError

class Command(BaseCommand):
    help = 'Test S3 connection and permissions'

    def handle(self, *args, **options):
        try:
            # Test S3 connection
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            
            # Test bucket access
            self.stdout.write("Testing S3 connection...")
            response = s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully connected to bucket: {bucket_name}"))
            
            # Test file upload WITHOUT ACL
            self.stdout.write("Testing file upload...")
            test_content = b"Test file content"
            s3_client.put_object(
                Bucket=bucket_name,
                Key='media/test/test_file.txt',
                Body=test_content
                # Removed ACL parameter
            )
            
            # Generate URL
            test_url = f"https://{bucket_name}.s3.amazonaws.com/media/test/test_file.txt"
            self.stdout.write(self.style.SUCCESS(f"✅ Test file uploaded: {test_url}"))
            
            # Test if file is publicly accessible
            import requests
            try:
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS("✅ File is publicly accessible"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ File uploaded but not publicly accessible (Status: {response.status_code})"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Could not test public access: {e}"))
            
            # Clean up test file
            s3_client.delete_object(Bucket=bucket_name, Key='media/test/test_file.txt')
            self.stdout.write("🗑️ Test file cleaned up")
            
            self.stdout.write(self.style.SUCCESS("🎉 S3 is configured correctly!"))
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                self.stdout.write(self.style.ERROR(f"❌ Bucket '{bucket_name}' does not exist"))
            elif error_code == 'AccessDenied':
                self.stdout.write(self.style.ERROR("❌ Access denied. Check your AWS credentials and bucket permissions"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ AWS Error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection error: {e}"))