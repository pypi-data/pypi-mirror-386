import json
import unittest

from uipath_langchain._tracing._oteladapter import LangChainExporter


class TestLangchainExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = LangChainExporter()

    def test_process_span_with_dict_attributes(self):
        """
        Tests that the span is processed correctly when Attributes is a dictionary.
        """
        span_data = {
            "Id": "501e2c8c-066a-43a8-8e14-7a8d51773a13",
            "TraceId": "8b706075-9bfc-452c-be10-766aa8827c35",
            "ParentId": "607b554d-f340-4cb7-9793-501d21c25bc1",
            "Name": "UiPathChat",
            "StartTime": "2025-09-18T14:35:47.523Z",
            "EndTime": "2025-09-18T14:35:48.988Z",
            "Attributes": {
                "input.value": '{"messages": [[{"lc": 1, "type": "constructor", "id": ["langchain", "schema", "messages", "HumanMessage"], "kwargs": {"content": "Test content", "type": "human"}}]]}',
                "output.value": '{"generations": []}',
                "llm.model_name": "gpt-4o-mini-2024-07-18",
                "openinference.span.kind": "LLM",
            },
            "Status": 1,
        }

        processed_span = self.exporter._process_span_attributes(span_data)

        self.assertEqual(processed_span["SpanType"], "completion")
        self.assertIn("Attributes", processed_span)

        attributes = json.loads(processed_span["Attributes"])
        self.assertEqual(attributes["model"], "gpt-4o-mini-2024-07-18")
        self.assertIn("input", attributes)
        self.assertIn("output", attributes)

    def test_process_span_with_json_string_attributes(self):
        """
        Tests that the span is processed correctly when Attributes is a JSON string.
        """
        attributes_dict = {
            "input.value": '{"messages": [[{"lc": 1, "type": "constructor", "id": ["langchain", "schema", "messages", "HumanMessage"], "kwargs": {"content": "Test content", "type": "human"}}]]}',
            "output.value": '{"generations": []}',
            "llm.model_name": "gpt-4o-mini-2024-07-18",
            "openinference.span.kind": "LLM",
        }
        span_data = {
            "Id": "501e2c8c-066a-43a8-8e14-7a8d51773a13",
            "TraceId": "8b706075-9bfc-452c-be10-766aa8827c35",
            "ParentId": "607b554d-f340-4cb7-9793-501d21c25bc1",
            "Name": "UiPathChat",
            "StartTime": "2025-09-18T14:35:47.523Z",
            "EndTime": "2025-09-18T14:35:48.988Z",
            "Attributes": json.dumps(attributes_dict),
            "Status": 1,
        }

        processed_span = self.exporter._process_span_attributes(span_data)

        self.assertEqual(processed_span["SpanType"], "completion")
        self.assertIn("Attributes", processed_span)

        attributes = json.loads(processed_span["Attributes"])
        self.assertEqual(attributes["model"], "gpt-4o-mini-2024-07-18")
        self.assertIn("input", attributes)
        self.assertIn("output", attributes)

    def test_process_tool_span(self):
        """
        Tests that a tool span is processed correctly.
        """
        span_data = {
            "Id": "b667e7d7-913f-4e99-8d95-1a7660e40edd",
            "TraceId": "8b706075-9bfc-452c-be10-766aa8827c35",
            "ParentId": "607b554d-f340-4cb7-9793-501d21c25bc1",
            "Name": "get_current_time",
            "StartTime": "2025-09-18T14:35:48.992Z",
            "EndTime": "2025-09-18T14:35:48.993Z",
            "Attributes": {
                "input.value": "{}",
                "output.value": "2025-09-18 14:35:48",
                "tool.name": "get_current_time",
                "openinference.span.kind": "TOOL",
            },
            "Status": 1,
        }

        processed_span = self.exporter._process_span_attributes(span_data)

        self.assertEqual(processed_span["SpanType"], "toolCall")
        self.assertIn("Attributes", processed_span)

        attributes = json.loads(processed_span["Attributes"])
        self.assertEqual(attributes["toolName"], "get_current_time")
        self.assertEqual(attributes["arguments"], {})
        self.assertEqual(attributes["result"], "2025-09-18 14:35:48")
        self.assertIn("input.value", attributes)
        self.assertIn("output.value", attributes)

    def test_process_span_attributes_tool_call(self):
        span_data = {
            "PermissionStatus": 0,
            "Id": "7ec33180-5fe5-49ec-87aa-03d5a1e9ccc7",
            "TraceId": "fde81e6a-cb40-496a-bff1-939b061dd6c9",
            "ParentId": "0babf3dd-aff3-4961-a8b3-1e7f64259832",
            "Name": "get_current_time",
            "StartTime": "2025-09-18T14:58:31.417Z",
            "EndTime": "2025-09-18T14:58:31.418Z",
            "Attributes": {
                "input.value": "{}",
                "output.value": "2025-09-18 14:58:31",
                "tool.name": "get_current_time",
                "tool.description": "Get the current date and time.",
                "session.id": "0b3cf051-6446-4467-a9a1-3b4b699f476b",
                "metadata": '{"thread_id": "0b3cf051-6446-4467-a9a1-3b4b699f476b", "langgraph_step": 1, "langgraph_node": "make_tool_calls", "langgraph_triggers": ["branch:to:make_tool_calls"], "langgraph_path": ["__pregel_pull", "make_tool_calls"], "langgraph_checkpoint_ns": "make_tool_calls:efdce94a-e49a-99f3-180a-f1b3e44f08f7", "checkpoint_ns": "make_tool_calls:efdce94a-e49a-99f3-180a-f1b3e44f08f7"}',
                "openinference.span.kind": "TOOL",
            },
            "Status": 1,
            "OrganizationId": "b7006b1c-11c3-4a80-802e-fee0ebf9c360",
            "TenantId": "6961a069-3392-40ca-bf5d-276f4e54c8ff",
            "ExpiryTimeUtc": None,
            "FolderKey": "d0e72980-7a97-44e1-93b7-4087689521b7",
            "Source": 0,
            "SpanType": "OpenTelemetry",
            "ProcessKey": "65965c09-87e3-4fa3-a7be-3fdb3955bd47",
            "JobKey": "0b3cf051-6446-4467-a9a1-3b4b699f476b",
            "ReferenceId": None,
            "VerbosityLevel": 2,
            "ExecutionType": None,
            "UpdatedAt": "2025-09-18T14:58:36.891Z",
        }

        processed_span = self.exporter._process_span_attributes(span_data)
        self.assertEqual(processed_span["SpanType"], "toolCall")

        attributes = json.loads(processed_span["Attributes"])
        self.assertEqual(attributes["toolName"], "get_current_time")
        self.assertEqual(attributes["input"], {})
        self.assertEqual(attributes["output"], "2025-09-18 14:58:31")

    def test_tool_span_mapping_issue(self):
        """
        Test the specific TOOL span that fails to map correctly.
        This reproduces the issue where TOOL spans don't get properly mapped.
        """
        span_data = {
            "PermissionStatus": 0,
            "Id": "79398bc6-f01f-424b-9238-342d71f38d3e",
            "TraceId": "731b01dd-ae81-4681-ad27-a56d33e80fe1",
            "ParentId": "2529b799-c3b9-4506-8e00-6824f6b5c30a",
            "Name": "get_current_time",
            "StartTime": "2025-09-18T15:14:19.639Z",
            "EndTime": "2025-09-18T15:14:19.640Z",
            "Attributes": {
                "input.value": "{}",
                "output.value": "2025-09-18 15:14:19",
                "tool.name": "get_current_time",
                "tool.description": "Get the current date and time.",
                "session.id": "8364fdaf-3915-414b-9f64-f90a62a7454c",
                "metadata": '{"thread_id": "8364fdaf-3915-414b-9f64-f90a62a7454c", "langgraph_step": 1, "langgraph_node": "make_tool_calls", "langgraph_triggers": ["branch:to:make_tool_calls"], "langgraph_path": ["__pregel_pull", "make_tool_calls"], "langgraph_checkpoint_ns": "make_tool_calls:1758151e-7e11-2f93-d853-06bf123710ca", "checkpoint_ns": "make_tool_calls:1758151e-7e11-2f93-d853-06bf123710ca"}',
                "openinference.span.kind": "TOOL",
            },
            "Status": 1,
            "OrganizationId": "b7006b1c-11c3-4a80-802e-fee0ebf9c360",
            "TenantId": "6961a069-3392-40ca-bf5d-276f4e54c8ff",
            "ExpiryTimeUtc": None,
            "FolderKey": "d0e72980-7a97-44e1-93b7-4087689521b7",
            "Source": 0,
            "SpanType": "OpenTelemetry",
            "ProcessKey": "65965c09-87e3-4fa3-a7be-3fdb3955bd47",
            "JobKey": "8364fdaf-3915-414b-9f64-f90a62a7454c",
            "ReferenceId": None,
            "VerbosityLevel": 2,
            "ExecutionType": None,
            "UpdatedAt": "2025-09-18T15:14:20.482Z",
        }

        processed_span = self.exporter._process_span_attributes(span_data)

        # SpanType should be mapped to toolCall
        self.assertEqual(processed_span["SpanType"], "toolCall")

        # Attributes should be processed
        self.assertIn("Attributes", processed_span)

        attributes = json.loads(processed_span["Attributes"])

        # These are the expected attributes for a tool call
        self.assertEqual(attributes["toolName"], "get_current_time")
        self.assertEqual(attributes["type"], "toolCall")
        self.assertEqual(attributes["arguments"], {})
        self.assertEqual(attributes["result"], "2025-09-18 15:14:19")
        self.assertEqual(attributes["toolType"], "Integration")
        self.assertIsNone(attributes["error"])

        # input.value should be mapped to input
        self.assertIn("input", attributes)
        self.assertEqual(attributes["input"], {})

    def test_llm_span_mapping_consistency(self):
        """
        Test that LLM spans are consistently mapped to completion type.
        This verifies the fix for flaky span type mapping.
        """
        span_data = {
            "PermissionStatus": 0,
            "Id": "8198780d-9d79-4270-b69d-aaf012189c50",
            "TraceId": "78e8f5a6-d694-456f-a639-ab161ac8ac5b",
            "ParentId": "c8c6e2bb-241b-429a-8471-95da8693a28f",
            "Name": "UiPathChat",
            "StartTime": "2025-09-18T15:25:36.486Z",
            "EndTime": "2025-09-18T15:25:37.720Z",
            "Attributes": {
                "input.value": '{"messages": []}',
                "output.value": '{"generations": []}',
                "llm.model_name": "gpt-4o-mini-2024-07-18",
                "llm.token_count.prompt": 219,
                "llm.token_count.completion": 66,
                "llm.token_count.total": 285,
                "openinference.span.kind": "LLM",
            },
            "Status": 1,
            "OrganizationId": "b7006b1c-11c3-4a80-802e-fee0ebf9c360",
            "TenantId": "6961a069-3392-40ca-bf5d-276f4e54c8ff",
            "ExpiryTimeUtc": None,
            "FolderKey": "d0e72980-7a97-44e1-93b7-4087689521b7",
            "Source": 0,
            "SpanType": "OpenTelemetry",
            "ProcessKey": "65965c09-87e3-4fa3-a7be-3fdb3955bd47",
            "JobKey": "04ecd5b3-72ef-4302-beae-7d21a94ab0de",
            "ReferenceId": None,
            "VerbosityLevel": 2,
            "ExecutionType": None,
            "UpdatedAt": "2025-09-18T15:25:38.591Z",
        }

        processed_span = self.exporter._process_span_attributes(span_data)

        # Verify LLM span gets mapped to completion
        self.assertEqual(processed_span["SpanType"], "completion")

        # Verify attributes are processed
        self.assertIn("Attributes", processed_span)

        attributes = json.loads(processed_span["Attributes"])

        # Verify LLM-specific attributes are present
        self.assertEqual(attributes["model"], "gpt-4o-mini-2024-07-18")
        self.assertIn("usage", attributes)
        self.assertEqual(attributes["usage"]["promptTokens"], 219)
        self.assertEqual(attributes["usage"]["completionTokens"], 66)
        self.assertEqual(attributes["usage"]["totalTokens"], 285)


if __name__ == "__main__":
    unittest.main()
