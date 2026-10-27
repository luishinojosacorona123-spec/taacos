"""Script automatizado para crear el Data Lake en Amazon S3 y subir las zonas raw/ y clean/.
Uso:
  1. Configura tus variables en el archivo .env (o pásalas por terminal)
  2. Ejecuta: python scripts/subir_a_aws.py
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    aws_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    aws_session_token = os.getenv("AWS_SESSION_TOKEN", "").strip()  # Por si usan AWS Academy Learner Lab
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1").strip()
    bucket_name = os.getenv("AWS_S3_BUCKET", "taacos-datalake-colima-2026").strip()

    if not aws_key or not aws_secret or aws_key == "TU_ACCESS_KEY_IAM_AQUI":
        print("❌ ERROR: Aún no has colocado tus llaves AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY en el archivo .env")
        sys.exit(1)

    session_kwargs = {
        "aws_access_key_id": aws_key,
        "aws_secret_access_key": aws_secret,
        "region_name": region,
    }
    if aws_session_token:
        session_kwargs["aws_session_token"] = aws_session_token

    s3 = boto3.client("s3", **session_kwargs)

    # 1. Crear el Bucket S3 (si no existe)
    print(f"🚀 Verificando / Creando bucket S3: '{bucket_name}' en la región '{region}'...")
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        print(f"✅ Bucket '{bucket_name}' creado exitosamente.")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"ℹ️ El bucket '{bucket_name}' ya existe y está listo.")
        else:
            print(f"❌ Error al crear el bucket: {e}")
            sys.exit(1)

    # 2. Subir archivo a la zona raw/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_local = os.path.join(base_dir, "raw", "portafolio_inmuebles_raw.csv")
    clean_local = os.path.join(base_dir, "clean", "portafolio_inmuebles_clean.csv")

    print("📤 Subiendo 'raw/portafolio_inmuebles_raw.csv' a S3 (zona raw/)...")
    s3.upload_file(raw_local, bucket_name, "raw/portafolio_inmuebles_raw.csv")
    print(f"✅ Subido: s3://{bucket_name}/raw/portafolio_inmuebles_raw.csv")

    # 3. Subir archivo a la zona clean/
    print("📤 Subiendo 'clean/portafolio_inmuebles_clean.csv' a S3 (zona clean/)...")
    s3.upload_file(clean_local, bucket_name, "clean/portafolio_inmuebles_clean.csv")
    print(f"✅ Subido: s3://{bucket_name}/clean/portafolio_inmuebles_clean.csv")

    # 4. Crear marcador de la zona models/ (para E3)
    s3.put_object(Bucket=bucket_name, Key="models/.keep", Body=b"")
    print(f"✅ Zona creada: s3://{bucket_name}/models/")

    # 5. Verificar objetos dentro del bucket
    resp = s3.list_objects_v2(Bucket=bucket_name)
    print("\n🎉 ¡DATA LAKE EN AWS S3 LISTO! Objetos actuales en el bucket:")
    for obj in resp.get("Contents", []):
        print(f"   - s3://{bucket_name}/{obj['Key']} ({obj['Size']} bytes)")


if __name__ == "__main__":
    main()
