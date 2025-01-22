from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    CfnOutput # Import CfnOutput
)
from constructs import Construct
import json

class PrivAceItEceCapstoneMainStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create a new VPC with 1 NAT Gateway
        my_vpc = ec2.Vpc(
            self,
            "MyVpc",
            max_azs=2,  # Creates subnets in 2 Availability Zones
            nat_gateways=1,  # Only 1 NAT gateway for cost savings
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                )
            ]
        )

        # 2. Create a Security Group for the Lambda
        lambda_sg = ec2.SecurityGroup(
            self,
            "LambdaSG",
            vpc=my_vpc,
            description="Security group for my Lambda function",
            allow_all_outbound=True  # let it call external services
        )

        my_rds_sg = ec2.SecurityGroup(
            self,
            "MyRdsSG",
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
            "MyRdsSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_template),  # Pass the structure of the secret as a JSON string
                generate_string_key="password",  # Key in the template to generate the password for
                exclude_punctuation=True,  # Optionally exclude punctuation from the generated password
                password_length=16  # Length of the generated password
            )
        )

        my_rds = rds.DatabaseInstance(
            self,
            "t4gRDSdb",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3
            ),
            instance_type=ec2.InstanceType("t4g.micro"),
            vpc=my_vpc,
            security_groups=[my_rds_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            credentials=rds.Credentials.from_secret(db_secret)
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

        # Define the Lambda function resources
        fetchReadFromS3 = _lambda.Function(
            self,
            "FetchReadFromS3Function",
            runtime=_lambda.Runtime.PYTHON_3_9,  # Use a Python runtime (e.g., Python 3.9)
            code=_lambda.Code.from_asset("lambda"),  # Points to the 'lambda' directory
            handler="fetchReadFromS3.lambda_handler",  # Points to the 'hello.py' file and 'handler' function
            layers=[langchain_layer, pymupdf_layer, other_text_related_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        recent_course_data_analysis = _lambda.Function(
            self,
            "RecentCourseDataAnalysisFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="recentCourseData.lambda_handler",
        )

        top_questions_lambda = _lambda.Function(
            self,
            "TopQuestionsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="topQuestions.lambda_handler",
        )

        top_materials_lambda = _lambda.Function(
            self,
            "TopMaterialsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="topMaterials.lambda_handler",
        )

        student_engagement_lambda = _lambda.Function(
            self,
            "StudentEngagementLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="studentEngagement.lambda_handler",
        )

        get_course_configuration_lambda = _lambda.Function(
            self,
            "GetCourseConfigLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getCourseConfig.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        update_course_configuration_lambda = _lambda.Function(
            self,
            "UpdateCourseConfigLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="updateCourseConfig.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        student_send_msg_lambda = _lambda.Function(
            self,
            "StudentSendMsgLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="studentSendMsg.lambda_handler",
        )

        get_user_info_lambda = _lambda.Function(
            self,
            "GetUserInfoLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getUserInfo.lambda_handler",
        )

        get_user_courses_lambda = _lambda.Function(
            self,
            "GetUserCoursesLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getUserCourses.lambda_handler",
        )

        login_lambda = _lambda.Function(
            self,
            "LoginLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="login.lambda_handler",
        )

        logout_lambda = _lambda.Function(
            self,
            "LogoutLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="logout.lambda_handler",
        )

        get_vector_lambda = _lambda.Function(
            self,
            "GetVectorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="getVector.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        add_vector_lambda = _lambda.Function(
            self,
            "AddVectorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="addVector.lambda_handler",
            layers=[langchain_layer, pymupdf_layer, other_text_related_layer, boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        delete_vector_lambda = _lambda.Function(
            self,
            "DeleteVectorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="deleteVector.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        refresh_content_lambda = _lambda.Function(
            self,
            "RefreshContentLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="refreshContent.lambda_handler",
        )

        delete_all_course_data_lambda = _lambda.Function(
            self,
            "DeleteAllCourseLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="deleteAllCourseData.lambda_handler",
            layers=[boto3_layer, psycopg_layer],
            vpc=my_vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        refresh_all_existing_courses_lambda = _lambda.Function(
            self,
            "RefreshAllCoursesLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="refreshAllCourses.lambda_handler",
        )

        generate_llm_prompt_lambda = _lambda.Function(
            self,
            "GenerateLLMPromptLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="generateLLMPrompt.lambda_handler",
        )

        invoke_llm_completion_lambda = _lambda.Function(
            self,
            "InvokeLLMComletionLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="invokeLLMCompletion.lambda_handler",
        )

        generate_llm_analysis_lambda = _lambda.Function(
            self,
            "GenerateLLMAnaysisLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),
            handler="generateLLMAnalysis.lambda_handler",
        )

        get_past_sessions_lambda = _lambda.Function(
            self,
            "GetPastSessionsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="getPastSessions.lambda_handler",
        )

        restore_past_session_lambda = _lambda.Function(
            self,
            "RestorePastSessionLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda"),  # Points to the lambda directory
            handler="restorePastSession.lambda_handler",
        )



        # Define the shared IAM role
        shared_policy_for_lambda = iam.Policy(
            self,
            "SharedPolicyForLambda",
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
                        # "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0",
                        # "arn:aws:secretsmanager:us-west-2:842676002045:secret:MyRdsSecretF2FB5411-KUVYnbkG81km-9gvCxv"
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

        recent_course_data_analysis.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],  # Add other required permissions here
                resources=["arn:aws:s3:::bucketforanalysisdata/*"]  # Adjust bucket name
            )
        )

        # Define the API Gateway resource
        api = apigateway.RestApi(
            self,
            "CourseAPI",
            rest_api_name="CourseAPI",
            description="API to handle course-related data"
        )

        # build resources
        api_resource = api.root.add_resource("api")
        ui_resource = api_resource.add_resource("ui")
        general_resource = ui_resource.add_resource("general")
        login_resource = general_resource.add_resource("log-in")
        logout_resource = general_resource.add_resource("log-out")
        user_resource = general_resource.add_resource("user")
        user_courses_resource = user_resource.add_resource("courses")
        student_resource = ui_resource.add_resource("student")
        session_resource = student_resource.add_resource("session")
        specific_session_resource = session_resource.add_resource("{sessionId}")
        student_send_msg_resource = student_resource.add_resource("send-message")
        instructor_resource = ui_resource.add_resource("instructor")
        instructor_config_resource = instructor_resource.add_resource("config")
        analytics_resource = instructor_resource.add_resource("analytics")
        top_questions_resource = analytics_resource.add_resource("top-questions")
        top_materials_resource = analytics_resource.add_resource("top-materials")
        student_engagement_resource = analytics_resource.add_resource("engagement")
        llm_resource = api_resource.add_resource("llm")
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
        # TODO: Figure out how log in works

        # GET /api/ui/student/session
        session_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_past_sessions_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        session_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/ui/student/session/sessionId
        specific_session_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(restore_past_session_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        specific_session_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )
 
        # POST /api/ui/general/log-out
        logout_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(logout_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        logout_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["POST"],
        )

        # GET /api/ui/general/user
        user_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_user_info_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        user_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )
 
        # GET /api/ui/general/user
        user_courses_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_user_courses_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        user_courses_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )
 
        # PUT /api/ui/instructor/config
        instructor_config_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(update_course_configuration_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )

        # GET /api/ui/instructor/config?course={uuid}
        instructor_config_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_course_configuration_lambda),
            request_parameters={
                "method.request.querystring.course": True,
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        instructor_config_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET", "PUT"],
        )
        
        # GET /api/ui/instructor/analytics/engagement
        student_engagement_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(student_engagement_lambda),
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
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        student_engagement_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/ui/instructor/analytics/top-materials
        top_materials_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(top_materials_lambda),
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
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        top_materials_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/ui/instructor/analytics/top-questions
        top_questions_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(top_questions_lambda),
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
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        top_questions_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/llm/content/canvas
        canvas_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(fetchReadFromS3),
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
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],  # Allowed methods
        )

        # GET /api/llm/analysis/data
        analysis_data_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(recent_course_data_analysis),
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
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )
        
        # POST /api/ui/student/send-message
        student_send_msg_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(student_send_msg_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        student_send_msg_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["POST"],
        )
 
        # GET /api/llm/vector
        vector_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(get_vector_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        # PUT /api/llm/vector
        vector_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(add_vector_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        # DELETE /api/llm/vector
        vector_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_vector_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        vector_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET", "POST", "DELETE"],
        )
 
        # POST /api/llm/content/refresh
        refresh_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(refresh_content_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        refresh_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["POST"],
        )

        # DELETE /api/llm/content
        content_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_all_course_data_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        content_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["DELETE"],
        )
 
        # GET /api/llm/content/refresh-existing-courses
        refresh_all_existing_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(refresh_all_existing_courses_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        refresh_all_existing_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/llm/chat/generate
        gen_chat_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(generate_llm_prompt_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        gen_chat_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/llm/completion
        llm_completion_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(invoke_llm_completion_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        llm_completion_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )

        # GET /api/llm/analysis/generate
        analysis_gen_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(generate_llm_analysis_lambda),
            request_parameters={
                "method.request.header.Authorization": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                apigateway.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
        )
        analysis_gen_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["Authorization", "Content-Type"],
            allow_methods=["GET"],
        )
