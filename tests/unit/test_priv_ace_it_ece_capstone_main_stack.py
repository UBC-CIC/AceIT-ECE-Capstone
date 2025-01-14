import aws_cdk as core
import aws_cdk.assertions as assertions

from priv_ace_it_ece_capstone_main.priv_ace_it_ece_capstone_main_stack import PrivAceItEceCapstoneMainStack

# example tests. To run these tests, uncomment this file along with the example
# resource in priv_ace_it_ece_capstone_main/priv_ace_it_ece_capstone_main_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PrivAceItEceCapstoneMainStack(app, "priv-ace-it-ece-capstone-main")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
