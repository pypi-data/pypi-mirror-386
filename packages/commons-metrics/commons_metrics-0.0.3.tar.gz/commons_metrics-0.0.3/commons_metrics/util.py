import boto3
import json
class Util:
    @staticmethod
    def get_secret_aws(env: str, logger):
        secret_name = f"nu0051005-measurement-systems-{env}-mesysqcd-secretrds-cnx1"
        region_name = "us-east-1"

        try:
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )

            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            secret_string = get_secret_value_response['SecretString']
            secret_json = json.loads(secret_string)

            required_keys = ["password", "host", "port", "username", "dbname"]
            missing_keys = [key for key in required_keys if key not in secret_json]

            if missing_keys:
                msg = f"Missing required keys in AWS secret: {missing_keys}"
                logger.error(msg)
                raise KeyError(msg)

            return secret_json

        except Exception as e:
            msg = f"Error getting the secret '{secret_name}': {str(e)}"
            logger.error(msg)
            raise Exception(msg)
        
    @staticmethod
    def show(env: str, logger):
        print("Hola mundo")