"""
测试 S3 连接和创建 bucket
"""
import boto3
from botocore.exceptions import ClientError
from config import settings

def test_s3_connection():
    """测试 S3 连接"""
    print("🔍 Testing S3 connection...")
    print(f"   Region: {settings.AWS_REGION}")
    print(f"   Bucket: {settings.AWS_S3_BUCKET}")
    
    try:
        # 创建 S3 客户端
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # 检查 bucket 是否存在
        try:
            s3.head_bucket(Bucket=settings.AWS_S3_BUCKET)
            print(f"✅ Bucket '{settings.AWS_S3_BUCKET}' exists!")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                print(f"⚠️  Bucket '{settings.AWS_S3_BUCKET}' does not exist. Creating...")
                
                # 创建 bucket
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        s3.create_bucket(Bucket=settings.AWS_S3_BUCKET)
                    else:
                        s3.create_bucket(
                            Bucket=settings.AWS_S3_BUCKET,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    
                    print(f"✅ Bucket '{settings.AWS_S3_BUCKET}' created successfully!")
                    
                    # 设置 CORS 配置
                    cors_configuration = {
                        'CORSRules': [{
                            'AllowedHeaders': ['*'],
                            'AllowedMethods': ['GET', 'PUT', 'POST'],
                            'AllowedOrigins': ['*'],
                            'ExposeHeaders': ['ETag'],
                            'MaxAgeSeconds': 3000
                        }]
                    }
                    s3.put_bucket_cors(
                        Bucket=settings.AWS_S3_BUCKET,
                        CORSConfiguration=cors_configuration
                    )
                    print("✅ CORS configuration set!")
                    
                except ClientError as create_error:
                    print(f"❌ Failed to create bucket: {create_error}")
                    return False
                    
            elif error_code == '403':
                print(f"❌ Access denied to bucket '{settings.AWS_S3_BUCKET}'")
                print("   Please check your AWS credentials and permissions.")
                return False
            else:
                print(f"❌ Error checking bucket: {e}")
                return False
        
        # 测试上传
        print("\n🧪 Testing file upload...")
        test_content = b"Test recording file"
        test_key = "recordings/test.wav"
        
        s3.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=test_key,
            Body=test_content,
            ContentType='audio/wav'
        )
        print(f"✅ Test file uploaded: {test_key}")
        
        # 生成预签名 URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET,
                'Key': test_key
            },
            ExpiresIn=3600
        )
        print(f"✅ Presigned URL generated:")
        print(f"   {url[:80]}...")
        
        # 清理测试文件
        s3.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=test_key)
        print(f"✅ Test file deleted")
        
        print("\n🎉 S3 configuration is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_s3_connection()
    exit(0 if success else 1)

