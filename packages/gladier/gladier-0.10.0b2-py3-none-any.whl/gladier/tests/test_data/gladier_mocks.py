from gladier import GladierBaseTool, GladierBaseClient
from gladier.decorators import generate_flow_definition

# Roughly simulates the look of a Globus Automate flow scope
mock_automate_flow_scope = (
    "https://auth.globus.org/scopes/mock_tool_flow_scope/"
    "flow_mock_tool_flow_scope_user"
)


def mock_func(data):
    """Test mock function"""
    pass


class MockTool(GladierBaseTool):
    flow_definition = {
        "Comment": "Say hello, maybe to a librarian.",
        "StartAt": "MockFunc",
        "States": {
            "MockFunc": {
                "Comment": "This func says the thing!",
                "Type": "Action",
                "ActionUrl": "https://compute.actions.globus.org",
                "ActionScope": "https://auth.globus.org/scopes/"
                "facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/automate2",
                "ExceptionOnActionFailure": False,
                "Parameters": {
                    "tasks": [
                        {
                            "endpoint.$": "$.input.compute_endpoint",
                            "func.$": "$.input.hello_world_function_id",
                            "payload.$": "$.input",
                        }
                    ]
                },
                "ResultPath": "$.HelloWorld",
                "WaitTime": 300,
                "End": True,
            },
        },
    }

    required_input = ["compute_endpoint"]

    flow_input = {"compute_endpoint": "my_compute_endpoint"}

    compute_functions = [
        mock_func,
    ]


@generate_flow_definition
class GeneratedTool(GladierBaseTool):
    compute_functions = [mock_func]


class MockToolWithRequirements(GladierBaseTool):
    required_input = ["compute_endpoint", "required_var"]
    flow_input = {
        "compute_endpoint": "my_compute_endpoint",
        "default_var": "is a thing!",
    }
    compute_functions = [
        mock_func,
    ]


class MockToolThreeStates(GladierBaseTool):
    flow_definition = {
        "Comment": "Do three things. Not two. Not four.",
        "StartAt": "StateOne",
        "States": {
            "StateOne": {
                "Comment": "Do the first thing",
                "Type": "Action",
                "ActionUrl": "https://compute.actions.globus.org",
                "ExceptionOnActionFailure": False,
                "Parameters": {
                    "tasks": [
                        {
                            "endpoint.$": "$.input.compute_endpoint",
                            "func.$": "$.input.hello_world_function_id",
                            "payload.$": "$.input.good_input",
                        }
                    ]
                },
                "ResultPath": "$.PublishGatherMetadata",
                "WaitTime": 60,
                "Next": "StateTwo",
            },
            "StateTwo": {
                "Comment": "Do the second thing",
                "Type": "Action",
                "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
                "InputPath": "$.StateOne.details.result.foo",
                "ResultPath": "$.StateTwo",
                "WaitTime": 600,
                "Next": "StateThree",
            },
            "StateThree": {
                "Comment": "Do the third thing",
                "Type": "Action",
                "ActionUrl": "https://actions.globus.org/search/ingest",
                "ExceptionOnActionFailure": False,
                "InputPath": "$.StateOne.details.result.bar",
                "ResultPath": "$.StateThree",
                "WaitTime": 300,
                "End": True,
            },
        },
    }

    required_input = ["compute_endpoint"]

    flow_input = {"compute_endpoint": "my_compute_endpoint"}


class MockToolChoiceState(GladierBaseTool):
    pass


class MockGladierClient(GladierBaseClient):
    secret_config_filename = "gladier-secrets.cfg"
    config_filename = "gladier.cfg"

    gladier_tools = ["gladier.tests.test_data.gladier_mocks.MockTool"]
    flow_definition = "gladier.tests.test_data.gladier_mocks.MockTool"
