import os
import boto3
from django.conf import settings

def check_s3_config():
    print("=== Checking S3 Configuration ===")
    
    # Print current configuration
    print("\nCurrent AWS Settings:")
    print(f"AWS_ACCESS_KEY_ID: {'*' * 10}{getattr(settings, 'AWS_ACCESS_KEY_ID', 'Not set')[-4:] if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else 'Not set'}")
    print(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
    print(f"AWS_S3_REGION_NAME: {getattr(settings, 'AWS_S3_REGION_NAME', 'Not set')}")
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
    print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
    print(f"MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'Not set')}")

    # Test S3 connection
    print("\nTesting S3 Connection...")
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # List buckets to test connection
        response = s3.list_buckets()
        print("✅ Successfully connected to S3")
        print("Available buckets:")
        for bucket in response.get('Buckets', []):
            print(f"  - {bucket['Name']}")
        
        # Check if the configured bucket exists
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' exists and is accessible")
            
            # Test upload
            test_key = 'test-upload.txt'
            print(f"\nTesting upload to '{bucket_name}/{test_key}'...")
            s3.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b'This is a test file',
                ContentType='text/plain'
            )
            print("✅ Successfully uploaded test file")
            
            # Generate URL
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': test_key},
                ExpiresIn=3600
            )
            print(f"\nTest file URL (valid for 1 hour):\n{url}")
            
        except Exception as e:
            print(f"❌ Error accessing bucket '{bucket_name}': {str(e)}")
            if "NoSuchBucket" in str(e):
                print("The specified bucket does not exist.")
            elif "AccessDenied" in str(e):
                print("You don't have permission to access this bucket.")
            
    except Exception as e:
        print(f"❌ Failed to connect to S3: {str(e)}")
        if "InvalidAccessKeyId" in str(e):
            print("The AWS Access Key ID is invalid.")
        elif "SignatureDoesNotMatch" in str(e):
            print("The AWS Secret Access Key is invalid.")
        elif "Region" in str(e):
            print("Invalid AWS region specified.")

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    check_s3_config()