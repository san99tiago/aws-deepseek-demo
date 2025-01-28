# Built-in imports
import os

# External imports
from aws_cdk import (
    Stack,
    aws_s3,
    aws_s3_deployment,
    triggers,
    RemovalPolicy,
    Duration,
)
from constructs import Construct
from aws_cdk import aws_lambda as lambda_


class BedrockCustomModelStack(Stack):
    """
    Class to create S3 buckets Bedrock Custom Models for Gen-AI building blocks.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        main_resources_name: str,
        app_config: dict[str],
        **kwargs,
    ) -> None:
        """
        :param scope (Construct): Parent of this stack, usually an 'App' or a 'Stage', but could be any construct.
        :param construct_id (str): The construct ID of this stack (same as aws-cdk Stack 'construct_id').
        :param main_resources_name (str): The main unique identified of this stack.
        :param app_config (dict[str]): Dictionary with relevant configuration values for the stack.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Input parameters
        self.construct_id = construct_id
        self.main_resources_name = main_resources_name
        self.app_config = app_config

        # Main methods for the deployment
        self.create_s3_buckets()

        # # TODO: refactor/update this steps in the future... Not quite just yet..
        # self.upload_objects_to_s3()
        # self.create_bedrock_custom_model()

    def create_s3_buckets(self):
        """
        Method to create S3 buckets.
        """
        self.bucket = aws_s3.Bucket(
            self,
            "Bucket",
            bucket_name=f"bedrock-custom-models-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            event_bridge_enabled=False,
        )

    # TODO: NOT VIABLE as files exceed 2GBs... Another approach must be done.
    def upload_objects_to_s3(self):
        """
        Method to upload object/files to S3 bucket at deployment.
        """
        PATH_TO_S3_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "ai-model",
            "model",
        )

        files_deployment_1 = aws_s3_deployment.BucketDeployment(
            self,
            "S3Deployment1",
            sources=[aws_s3_deployment.Source.asset(PATH_TO_S3_FOLDER)],
            destination_bucket=self.bucket,
            destination_key_prefix=self.app_config["model_name"],
        )

    # TODO: Even if we have this Lambda, we can not fully use it, as the necessary
    # ... underlying SDKs are not available for "ImportCustomModel" APIs
    def create_bedrock_custom_model(self):
        """
        Method to create Bedrock Resources.
        """
        # Get relative path for folder that contains Lambda function source
        # ! Note--> we must obtain parent dirs to create path (that"s why there is "os.path.dirname()")
        PATH_TO_LAMBDA_FUNCTION_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "lambdas",
        )

        # The whole purpose of this function is to run the Bedrock code to import the model from the S3 bucket
        post_deployment_trigger = triggers.TriggerFunction(
            self,
            "PostDeploymentTrigger",
            runtime=lambda_.Runtime.PYTHON_3_11,
            function_name=f"{self.main_resources_name}-post-deployment-trigger",
            memory_size=1024,
            handler="lambda_function.handler",
            code=PATH_TO_LAMBDA_FUNCTION_FOLDER,
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
            },
            timeout=Duration.seconds(60),
        )
        self.bucket.grant_read(post_deployment_trigger)
