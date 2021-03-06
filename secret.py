# !/bin/env python
import json, os, boto3, base64
from botocore.exceptions import ClientError

def getSecretKeys():
    """Returns only the secret manager environment variables"""
    secretKeys = dict()
    for (key, value) in os.environ.items():
        if( key.startswith("SM_")):
            secretKeys[key] = value
    if(bool(secretKeys)):
        return secretKeys
    else:
        raise ValueError("Secrets Manager environment variable key not found, make sure there is atleast an env var with 'SM_' prefix for the init-container")

def getSecretFileName():
    secretFile = os.environ["SECRET_FILE_PATH"]
    return secretFile

def get_secret(secret_name):
    region_name = os.environ["AWS_REGION"]
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name,
            VersionStage="AWSCURRENT"
        )
    except ClientError as e:
        raise e
    else:
        if 'SecretString' in get_secret_value_response and get_secret_value_response['SecretString']:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret

def loadSecret(prefix, secret_name, secretFile):
    print("Saving", secret_name, "secrets to", secretFile.name)
    data=get_secret(secret_name)
    secret = json.loads(data)
    # Mocking the response for testing locally
    # secret = {
    #             "username": "admin",
    #             "engine": "mysql",
    #             "dbClusterIdentifier": "test-aurora-db",
    #             "host": "test-aurora-db.cluster-xxxxxxxxxxxxxx.ap-southeast-1.rds.amazonaws.com",
    #             "password": "8h?o[R;2qZMa)Tbq[Pt69AhjXFx#X$*>",
    #             "port": 3306
    #         }
    for key, value in secret.items():
        secretFile.write(prefix + key.upper() + "=" + "'" + str(value) + "'" + "\n")
    print("Done fetching secrets", secret_name)

print("Running init container script")
allSecrets = getSecretKeys()
secretFileName = getSecretFileName()
secretFile = open(secretFileName,"w")
try:
    for (key, secret_name) in allSecrets.items():
        prefix = key.split("_")[1] + "_"
        loadSecret(prefix, secret_name, secretFile)
finally:
    secretFile.close()
    print("Exiting init container script")
