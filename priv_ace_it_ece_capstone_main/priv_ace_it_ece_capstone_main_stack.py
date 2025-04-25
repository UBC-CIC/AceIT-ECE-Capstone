from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
    SecretValue,
    aws_s3_notifications as s3_notifications,
    CfnOutput # Import CfnOutput
)
from constructs import Construct
import json

class PrivAceItEceCapstoneMainStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_prefix, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an S3 Bucket
        course_doc_bucket = s3.Bucket(
            self,
            # "CourseDocumentsBucket",
            f"{env_prefix}CourseDocumentsBucket",
            bucket_name=f"{env_prefix}bucket-for-course-documents",
            versioned=True,  # Enable versioning
            removal_policy=RemovalPolicy.DESTROY,  # Delete on stack removal
            auto_delete_objects=True
        )

        # 1. Create a new VPC with 1 NAT Gateway
        my_vpc = ec2.Vpc(
            self,
            f"{env_prefix}MyVpc",
            max_azs=2,  # Creates subnets in 2 Availability Zones
            nat_gateways=1,  # Only 1 NAT gateway for cost savings
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{env_prefix}PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name=f"{env_prefix}PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                )
            ]
        )

        # 2. Create a Security Group for the Lambda
        lambda_sg = ec2.SecurityGroup(
            self,
            f"{env_prefix}LambdaSG",
            vpc=my_vpc,
            description="Security group for my Lambda function",
            allow_all_outbound=True  # let it call external services
        )

        my_rds_sg = ec2.SecurityGroup(
            self,
            f"{env_prefix}MyRdsSG",
            vpc=my_vpc,
            description="Security group for RDS"
        )
        # Allow inbound from Lambda SG on PostgreSQL port 5432, for example
        my_rds_sg.add_ingress_rule(lambda_sg, ec2.Port.tcp(5432), "Allow Lambda access to DB")

        secret_template = {
            "username": "rdsdbadmin",  # Placeholder for the username
            "password": ""   # Placeholder for the password to be generated
        }

        # Create the secret in Secrets Manager for DB credentials
        db_secret = secretsmanager.Secret(
            self,
            f"{env_prefix}RdsDBSecret",
            secret_name=f"{env_prefix}RdsDBSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_template),  # Pass the structure of the secret as a JSON string
                generate_string_key="password",  # Key in the template to generate the password for
                exclude_punctuation=True,  # Optionally exclude punctuation from the generated password
                password_length=16  # Length of the generated password
            )
        )

        my_rds = rds.DatabaseInstance(
            self,
            f"{env_prefix}t4gRDSdb",
            database_name=f"{env_prefix}t4gRDSdb",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3
            ),
            instance_type=ec2.InstanceType("t4g.micro"),
            vpc=my_vpc,
            security_groups=[my_rds_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            credentials=rds.Credentials.from_secret(db_secret),
            removal_policy=RemovalPolicy.DESTROY  # Allow recreation of the resource
        )

        # Security Group for RDS Proxy
        rds_proxy_sg = ec2.SecurityGroup(
            self,
            f"{env_prefix}RdsProxySG",
            security_group_name=f"{env_prefix}RdsProxySG",
            vpc=my_vpc,
            description="Security group for RDS Proxy"
        )
        rds_proxy_sg.add_ingress_rule(lambda_sg, ec2.Port.tcp(5432), "Allow Lambda access to RDS Proxy")
        my_rds_sg.add_ingress_rule(rds_proxy_sg, ec2.Port.tcp(5432), "Allow RDS Proxy to access RDS")

        # RDS Proxy
        rds_proxy = rds.DatabaseProxy(
            self,
            f"{env_prefix}RdsProxy",
            db_proxy_name=f"{env_prefix}RdsProxy",
            proxy_target=rds.ProxyTarget.from_instance(my_rds),
            secrets=[db_secret],
            vpc=my_vpc,
            security_groups=[rds_proxy_sg],
            require_tls=True,
            idle_client_timeout=Duration.minutes(30),
            debug_logging=False
        )

        # Update Lambda Security Group to allow outbound to RDS Proxy
        lambda_sg.add_ingress_rule(rds_proxy_sg, ec2.Port.tcp(5432), "Allow RDS Proxy to access Lambda")

        # Create the Messages Table
        messages_table = dynamodb.Table(
            self, f"{env_prefix}MessagesTable",
            table_name=f"{env_prefix}Messages",  # Custom name for the table
            partition_key=dynamodb.Attribute(
                name="message_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # Change to RETAIN for production
        )
        messages_table.add_global_secondary_index(
            index_name="CourseIdIndex",
            partition_key=dynamodb.Attribute(
                name="course_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Create the Conversations Table
        conversations_table = dynamodb.Table(
            self, f"{env_prefix}ConversationsTable",
            table_name=f"{env_prefix}Conversations",  # Custom name for the table
            partition_key=dynamodb.Attribute(
                name="conversation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # Change to RETAIN for production
        )
        conversations_table.add_global_secondary_index(
            index_name="CourseStudentIndex",
            partition_key=dynamodb.Attribute(
                name="course_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="student_id",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Create the User Table
        users_table = dynamodb.Table(
            self, f"{env_prefix}UserTable",
            table_name=f"{env_prefix}Users",  # Custom name for the table
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # Change to RETAIN for production
        )

        # Set up layers for lambda functions
        pymupdf_layer = _lambda.LayerVersion(
            self, 
            "PymuPDFLayer",
            code=_lambda.Code.from_asset("layers/pymupdf-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        langchain_layer = _lambda.LayerVersion(
            self, 
            "LangChainLayer",
            code=_lambda.Code.from_asset("layers/langchain-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        other_text_related_layer = _lambda.LayerVersion(
            self, 
            "TextRelatedLayer",
            code=_lambda.Code.from_asset("layers/othertextformat-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        boto3_layer = _lambda.LayerVersion(
            self, 
            "BotoLayer",
            code=_lambda.Code.from_asset("layers/boto3-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        psycopg_layer = _lambda.LayerVersion(
            self, 
            "PsycopgLayer",
            code=_lambda.Code.from_asset("layers/psycopg-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        requests_layer = _lambda.LayerVersion(
            self, 
            "RequestsLayer",
            code=_lambda.Code.from_asset("layers/requests-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        jwt_layer = _lambda.LayerVersion(
            self, 
            "JWTLayer",
            code=_lambda.Code.from_asset("layers/jwt-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        )

        # Define the Lambda function resources
        fetchReadFromS3 = _lambda.Function(
            self,
            f"{env_prefix}FetchReadFromS3Function",
            runtime=_lambda.Runtime.PYTHON_3_9,  # Use a Python runtime (e.g., Python 3.9)
            function_name=f"{env_prefix}FetchReadFromS3Function",
            code=_lambda.Code.from_asset("lambda"),  # Points to the 'lambda' directory
            handler="fetchReadFromS3.lambda_handler",  # Points to the 'hello.py' file and 'handler' function
            layers=[langchain_layer, pymupdf_layer, other_text_related_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,  # Increase from 128MB to 512MB/1024MB/1536MB as needed
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        recent_course_data_analysis = _lambda.Function(
            self,
            f"{env_prefix}RecentCourseDataAnalysisFunction",
            function_name=f"{env_prefix}RecentCourseDataAnalysisFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="recentCourseData.lambda_handler",
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        top_questions_lambda = _lambda.Function(
            self,
            f"{env_prefix}TopQuestionsLambda",
            function_name=f"{env_prefix}TopQuestionsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="topQuestions.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        top_materials_lambda = _lambda.Function(
            self,
            f"{env_prefix}TopMaterialsLambda",
            function_name=f"{env_prefix}TopMaterialsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="topMaterials.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        student_engagement_lambda = _lambda.Function(
            self,
            f"{env_prefix}StudentEngagementLambda",
            function_name=f"{env_prefix}StudentEngagementLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="studentEngagement.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        get_course_configuration_lambda = _lambda.Function(
            self,
            f"{env_prefix}GetCourseConfigLambda",
            function_name=f"{env_prefix}GetCourseConfigLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getCourseConfig.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        update_course_configuration_lambda = _lambda.Function(
            self,
            f"{env_prefix}UpdateCourseConfigLambda",
            function_name=f"{env_prefix}UpdateCourseConfigLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="updateCourseConfig.lambda_handler",
            layers=[boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        update_conversation_prompts_lambda = _lambda.Function(
            self,
            f"{env_prefix}UpdateConversationPromptLambda",
            function_name=f"{env_prefix}UpdateConversationPromptLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="updateConversationPrompts.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        student_send_msg_lambda = _lambda.Function(
            self,
            f"{env_prefix}StudentSendMsgLambda",
            function_name=f"{env_prefix}StudentSendMsgLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="studentSendMsg.lambda_handler",
            layers=[langchain_layer, pymupdf_layer, other_text_related_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        get_user_info_lambda = _lambda.Function(
            self,
            f"{env_prefix}GetUserInfoLambda",
            function_name=f"{env_prefix}GetUserInfoLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getUserInfo.lambda_handler",
            layers=[langchain_layer, boto3_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        update_user_language_lambda = _lambda.Function(
            self,
            f"{env_prefix}UpdateUserLanguageLambda",
            function_name=f"{env_prefix}UpdateUserLanguageLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="updateUserLanguage.lambda_handler",
            layers=[langchain_layer, boto3_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        get_user_courses_lambda = _lambda.Function(
            self,
            f"{env_prefix}GetUserCoursesLambda",
            function_name=f"{env_prefix}GetUserCoursesLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getUserCourses.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        login_lambda = _lambda.Function(
            self,
            f"{env_prefix}LoginLambda",
            function_name=f"{env_prefix}LoginLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="login.lambda_handler",
            layers=[boto3_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        refresh_token_lambda = _lambda.Function(
            self,
            f"{env_prefix}RefreshTokenLambda",
            function_name=f"{env_prefix}RefreshTokenLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="refreshToken.lambda_handler",
            layers=[boto3_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        logout_lambda = _lambda.Function(
            self,
            f"{env_prefix}LogoutLambda",
            function_name=f"{env_prefix}LogoutLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="logout.lambda_handler",
            layers=[boto3_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        get_vector_lambda = _lambda.Function(
            self,
            f"{env_prefix}GetVectorLambda",
            function_name=f"{env_prefix}GetVectorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getVector.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        add_vector_lambda = _lambda.Function(
            self,
            f"{env_prefix}AddVectorLambda",
            function_name=f"{env_prefix}AddVectorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="addVector.lambda_handler",
            layers=[langchain_layer, pymupdf_layer, other_text_related_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        delete_vector_lambda = _lambda.Function(
            self,
            f"{env_prefix}DeleteVectorLambda",
            function_name=f"{env_prefix}DeleteVectorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="deleteVector.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        refresh_content_lambda = _lambda.Function(
            self,
            f"{env_prefix}RefreshContentLambda",
            function_name=f"{env_prefix}RefreshContentLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="refreshContent.lambda_handler",
            layers=[boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        delete_all_course_data_lambda = _lambda.Function(
            self,
            f"{env_prefix}DeleteAllCourseLambda",
            function_name=f"{env_prefix}DeleteAllCourseLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="deleteAllCourseData.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        refresh_all_existing_courses_lambda = _lambda.Function(
            self,
            f"{env_prefix}RefreshAllCoursesLambda",
            function_name=f"{env_prefix}RefreshAllCoursesLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="refreshAllCourses.lambda_handler",
            layers=[boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        generate_llm_prompt_lambda = _lambda.Function(
            self,
            f"{env_prefix}GenerateLLMPromptLambda",
            function_name=f"{env_prefix}GenerateLLMPromptLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="generateLLMPrompt.lambda_handler",
            layers=[boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        invoke_llm_completion_lambda = _lambda.Function(
            self,
            f"{env_prefix}InvokeLLMCompletionLambda",
            function_name=f"{env_prefix}InvokeLLMCompletionLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="invokeLLMCompletion.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        generate_llm_analysis_lambda = _lambda.Function(
            self,
            f"{env_prefix}GenerateLLMAnaysisLambda",
            function_name=f"{env_prefix}GenerateLLMAnaysisLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="generateLLMAnalysis.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        generate_suggestions_lambda = _lambda.Function(
            self,
            f"{env_prefix}GenerateSuggestionsLambda",
            function_name=f"{env_prefix}GenerateSuggestionsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="generateSuggestions.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer, other_text_related_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            memory_size=256,
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        get_past_sessions_lambda = _lambda.Function(
            self,
            f"{env_prefix}GetPastSessionsLambda",
            function_name=f"{env_prefix}GetPastSessionsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="getPastSessions.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer, requests_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        restore_past_session_lambda = _lambda.Function(
            self,
            f"{env_prefix}RestorePastSessionLambda",
            function_name=f"{env_prefix}RestorePastSessionLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="restorePastSession.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        get_all_materials_lambda = _lambda.Function(
            self,
            f"{env_prefix}GetAllMaterialsLambda",
            function_name=f"{env_prefix}GetAllMaterialsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="getAllMaterials.lambda_handler",
            layers=[langchain_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            timeout=Duration.minutes(15),
            environment={
                "ENV_PREFIX": env_prefix
            },
        )

        # Define the shared IAM role
        shared_policy_for_lambda = iam.Policy(
            self,
            f"{env_prefix}SharedPolicyForLambda",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        # "s3:GetObject",
                        # "s3:ListBucket",
                        # "bedrock:InvokeModel",
                        # "secretsmanager:GetSecretValue"
                        "*"
                    ],
                    resources=[
                        # "arn:aws:s3:::bucketfortextextract",     # Needed for ListBucket
                        # "arn:aws:s3:::bucketfortextextract/*",    # Needed for GetObject
                        "*"
                    ]
                )
            ]
        )
        shared_policy_for_lambda.attach_to_role(fetchReadFromS3.role)
        shared_policy_for_lambda.attach_to_role(get_course_configuration_lambda.role)
        shared_policy_for_lambda.attach_to_role(update_course_configuration_lambda.role)
        shared_policy_for_lambda.attach_to_role(get_vector_lambda.role)
        shared_policy_for_lambda.attach_to_role(delete_vector_lambda.role)
        shared_policy_for_lambda.attach_to_role(add_vector_lambda.role)
        shared_policy_for_lambda.attach_to_role(delete_all_course_data_lambda.role)
        shared_policy_for_lambda.attach_to_role(refresh_content_lambda.role)
        shared_policy_for_lambda.attach_to_role(refresh_all_existing_courses_lambda.role)
        shared_policy_for_lambda.attach_to_role(invoke_llm_completion_lambda.role)
        shared_policy_for_lambda.attach_to_role(student_send_msg_lambda.role)
        shared_policy_for_lambda.attach_to_role(get_past_sessions_lambda.role)
        shared_policy_for_lambda.attach_to_role(restore_past_session_lambda.role)
        shared_policy_for_lambda.attach_to_role(top_questions_lambda.role)
        shared_policy_for_lambda.attach_to_role(top_materials_lambda.role)
        shared_policy_for_lambda.attach_to_role(student_engagement_lambda.role)
        shared_policy_for_lambda.attach_to_role(generate_llm_prompt_lambda.role)
        shared_policy_for_lambda.attach_to_role(generate_llm_analysis_lambda.role)
        shared_policy_for_lambda.attach_to_role(get_user_courses_lambda.role)
        shared_policy_for_lambda.attach_to_role(get_user_info_lambda.role)
        shared_policy_for_lambda.attach_to_role(login_lambda.role)
        shared_policy_for_lambda.attach_to_role(logout_lambda.role)
        shared_policy_for_lambda.attach_to_role(refresh_token_lambda.role)
        shared_policy_for_lambda.attach_to_role(update_conversation_prompts_lambda.role)
        shared_policy_for_lambda.attach_to_role(update_user_language_lambda.role)
        shared_policy_for_lambda.attach_to_role(generate_suggestions_lambda.role)
        shared_policy_for_lambda.attach_to_role(get_all_materials_lambda.role)

        recent_course_data_analysis.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],  # Add other required permissions here
                resources=["arn:aws:s3:::bucketforanalysisdata/*"]  # Adjust bucket name
            )
        )

        # Define the API Gateway resource
        api = apigateway.RestApi(
            self,
            f"{env_prefix}CourseAPI",
            rest_api_name=f"{env_prefix}CourseAPI",
            description="API to handle course-related data",
            endpoint_configuration={
                "types": [apigateway.EndpointType.REGIONAL]  # Ensures timeout increase works
            },
            # default_cors_preflight_options={
            #     "allow_origins": ["https://d2rs0jk5lfd7j4.cloudfront.net"],
            #     "allow_methods": ["OPTIONS", "GET", "POST"],
            #     "allow_headers": ["Content-Type", "Authorization"],
            #     "allow_credentials": True
            # }
        )

        # build resources
        api_resource = api.root.add_resource("api")
        ui_resource = api_resource.add_resource("ui")
        general_resource = ui_resource.add_resource("general")
        login_resource = general_resource.add_resource("log-in")
        refresh_token_resource = general_resource.add_resource("refresh-token")
        logout_resource = general_resource.add_resource("log-out")
        user_resource = general_resource.add_resource("user")
        user_language_resource = user_resource.add_resource("language")
        user_courses_resource = user_resource.add_resource("courses")
        student_resource = ui_resource.add_resource("student")
        session_resource = student_resource.add_resource("sessions")
        specific_session_resource = student_resource.add_resource("session")
        student_send_msg_resource = student_resource.add_resource("send-message")
        instructor_resource = ui_resource.add_resource("instructor")
        instructor_all_materials = instructor_resource.add_resource("all-materials")
        instructor_config_resource = instructor_resource.add_resource("config")
        update_system_prompt_resource = instructor_config_resource.add_resource("update-prompt")
        analytics_resource = instructor_resource.add_resource("analytics")
        top_questions_resource = analytics_resource.add_resource("top-questions")
        top_materials_resource = analytics_resource.add_resource("top-materials")
        student_engagement_resource = analytics_resource.add_resource("engagement")
        llm_resource = api_resource.add_resource("llm")
        suggestions_resource = llm_resource.add_resource("suggestions")
        vector_resource = llm_resource.add_resource("vector")
        content_resource = llm_resource.add_resource("content")
        refresh_resource = content_resource.add_resource("refresh")
        refresh_all_existing_resource = content_resource.add_resource("refresh-existing-courses")
        analysis_resource = llm_resource.add_resource("analysis")
        analysis_data_resource = analysis_resource.add_resource("data")
        analysis_gen_resource = analysis_resource.add_resource("generate")
        canvas_resource = content_resource.add_resource("canvas")
        gen_chat_resource = llm_resource.add_resource("chat").add_resource("generate")
        llm_completion_resource = llm_resource.add_resource("completion")

        # POST /api/ui/general/log-in
        login_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(login_lambda, proxy=True, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,  # Allow Headers
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                    },
                ),
            ],
        )

        login_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["OPTIONS", "POST"],  # Ensure OPTIONS is allowed
        )

        # POST /api/ui/general/refresh-token
        refresh_token_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(refresh_token_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        refresh_token_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["OPTIONS", "POST"],
        )

        # GET /api/ui/student/sessions
        session_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_past_sessions_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        session_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # GET /api/ui/student/session/sessionId
        specific_session_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(restore_past_session_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        specific_session_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )
 
        # POST /api/ui/general/log-out
        logout_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(logout_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        logout_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["OPTIONS","POST"],
        )

        # GET /api/ui/general/user
        user_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_user_info_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        user_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # PUT /api/ui/general/user/language
        user_language_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(update_user_language_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        user_language_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["PUT"],
        )
 
        # GET /api/ui/general/user/courses
        user_courses_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_user_courses_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        user_courses_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )
 
        # PUT /api/ui/instructor/config
        instructor_config_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(update_course_configuration_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )

        # GET /api/ui/instructor/config?course={uuid}
        instructor_config_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_course_configuration_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.querystring.course": True,
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        instructor_config_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET", "PUT"],
        )

        # GET /api/ui/instructor/config?course={uuid}
        instructor_all_materials.add_method(
            "GET",
            apigateway.LambdaIntegration(get_all_materials_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.querystring.course": True,
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        instructor_all_materials.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"]
        )


        # POST /api/ui/instructor/config/update-prompt
        update_system_prompt_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(update_conversation_prompts_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.querystring.course": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        update_system_prompt_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["POST"],
        )
        
        # GET /api/ui/instructor/analytics/engagement
        student_engagement_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(student_engagement_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.querystring.course": True,
                "method.request.querystring.period": True,
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        student_engagement_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # GET /api/ui/instructor/analytics/top-materials
        top_materials_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(top_materials_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.querystring.course": True,
                "method.request.querystring.num": True,
                "method.request.querystring.period": True,
                "method.request.header.Authorization": True
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        top_materials_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # GET /api/ui/instructor/analytics/top-questions
        top_questions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(top_questions_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.querystring.course": True,
                "method.request.querystring.num": True,
                "method.request.querystring.period": True,
                "method.request.header.Authorization": True
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        top_questions_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # GET /api/llm/content/canvas
        canvas_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(fetchReadFromS3, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )
        canvas_resource.add_cors_preflight(
            allow_origins=["*"],  # Replace "*" with your allowed origin if more restrictive
            allow_headers=["*"],
            allow_methods=["GET"],  # Allowed methods
        )

        # GET /api/llm/analysis/data
        analysis_data_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(recent_course_data_analysis, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )
        analysis_data_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )
        
        # POST /api/ui/student/send-message
        student_send_msg_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(student_send_msg_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        student_send_msg_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["POST"],
        )
 
        # GET /api/llm/vector
        vector_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_vector_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        # PUT /api/llm/vector
        vector_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(add_vector_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        # DELETE /api/llm/vector
        vector_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_vector_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        vector_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET", "POST", "DELETE"],
        )
 
        # POST /api/llm/content/refresh
        refresh_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(refresh_content_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        refresh_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["POST"],
        )

        # DELETE /api/llm/content
        content_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_all_course_data_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        content_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["DELETE"],
        )
 
        # GET /api/llm/content/refresh-existing-courses
        refresh_all_existing_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(refresh_all_existing_courses_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
            
        )
        refresh_all_existing_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # POST /api/llm/chat/generate
        gen_chat_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(generate_llm_prompt_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        gen_chat_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # GET /api/llm/completion
        llm_completion_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(invoke_llm_completion_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        llm_completion_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        suggestions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(generate_suggestions_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        suggestions_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )

        # GET /api/llm/analysis/generate
        analysis_gen_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(generate_llm_analysis_lambda, timeout=Duration.seconds(120)),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Credentials": True
                    }
                )
            ]
        )
        analysis_gen_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["GET"],
        )


        # Create an EventBridge rule that runs every 24 hours
        rule = events.Rule(
            self, f"{env_prefix}DailyTrigger",
            schedule=events.Schedule.rate(Duration.hours(24))  # Run every 24 hours
        )

        # Set the Lambda as the target for the rule
        rule.add_target(targets.LambdaFunction(refresh_all_existing_courses_lambda))