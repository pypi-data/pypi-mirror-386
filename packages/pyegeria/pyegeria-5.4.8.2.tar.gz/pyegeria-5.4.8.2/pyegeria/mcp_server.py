"""PDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.

This module provides a basic MCP server for Egeria.
"""
import re
import sys
import nest_asyncio

from typing import Any, Dict, Optional

from mcp.server.fastmcp.exceptions import ValidationError

from pyegeria.egeria_tech_client import EgeriaTech
from pyegeria._exceptions_new import print_validation_error


GLOBAL_EGERIA_CLIENT: Optional[EgeriaTech] = None
nest_asyncio.apply()

try:
    # We use Optional[] and List[] types, so we import them.
    from mcp.server.fastmcp import FastMCP
    from pyegeria.mcp_adapter import (
        list_reports,
        describe_report,
        run_report, _execute_egeria_call_blocking,
        _async_run_report_tool
    )
    print("MCP import successful...", file=sys.stderr)
except ImportError:
    print("MCP import failed.", file=sys.stderr)
    raise

def _ok(result: Dict[str, Any] ) -> Dict[str, Any]:
    # Pass-through helper in case you want to normalize or add metadata
    print("OK: Operation completed successfully.", file=sys.stderr)
    return result


def main() -> None:
    # Initialize the server

    global GLOBAL_EGERIA_CLIENT

    try:
        """ Runs ONCE when the server starts.
            Initializes the Egeria client and stores it in the server's state.
        """
        print("DEBUG: Initializing Egeria client...", file=sys.stderr)
        from pyegeria.config import settings as _settings
        user_id = _settings.User_Profile.user_name
        user_pwd = _settings.User_Profile.user_pwd

        GLOBAL_EGERIA_CLIENT = EgeriaTech(
            _settings.Environment.egeria_view_server,
            _settings.Environment.egeria_view_server_url,
            user_id,
            user_pwd
        )
        print("DEBUG: Egeria Client initialized", file=sys.stderr)
        GLOBAL_EGERIA_CLIENT.create_egeria_bearer_token("erinoverview","secret")
        print("DEBUG: Egeria Client connected", file=sys.stderr)

    except ValidationError as e:
        print_validation_error(e)
        raise
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}", file=sys.stderr)
        raise

    srv = FastMCP(name="pyegeria-mcp")
    print("Starting MCP server...", file=sys.stderr)

    # list_reports tool (formerly list_format_sets)
    @srv.tool(name="list_reports")
    def list_reports_tool() -> Dict[str, Any]:
        """Lists all available reports (FormatSets)."""
        print("DEBUG: Listing reports...", file=sys.stderr)
        return _ok(list_reports())

    # describe_report tool (formerly describe_format_set)
    @srv.tool(name="describe_report")
    def describe_report_tool(name: str, output_type: str = "DICT") -> Dict[str, Any]:
        """Returns the schema and details for a specified report."""
        # FastMCP handles validation of 'name' and 'output_type' types automatically.
        print(f"DEBUG: Describing report: {name} with output type: {output_type}", file=sys.stderr)
        try:
            return _ok(describe_report(name, output_type))
        except Exception as e:
            print(f"DEBUG: Exception during describe_report: {str(e)}", file=sys.stderr)
            raise

    @srv.tool(name="run_report")
    async def run_report_tool(
            report_name: str,
            search_string: str = "*",
            page_size: Optional[int] = None,
            start_from: Optional[int] = None,
            starts_with: Optional[bool] = None,
            ends_with: Optional[bool] = None,
            ignore_case: Optional[bool] = None,
            output_format: str = "DICT"
    ) -> Dict[str, Any]:
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()

        """Run a report with the specified parameters."""
        print("DEBUG: Running report...", file=sys.stderr)
        # 1. Automatic Validation: FastMCP/Pydantic ensures types are correct.

        # 2. Manual Validation (for specific values like output_format)
        if output_format not in ["DICT", "JSON", "REPORT", "MERMAID", "HTML"]:
            print(f"DEBUG: Invalid output_format: {output_format}", file=sys.stderr)
            raise ValueError(
                f"Invalid output_format: {output_format}. Must be one of ['DICT', 'JSON', 'REPORT', 'MERMAID', 'HTML'].")

        # 3. Build params dictionary with only non-None values for clean passing
        params = {
            "search_string": search_string,
            "page_size": page_size,
            "start_from": start_from,
            "starts_with": starts_with,
            "ends_with": ends_with,
            "ignore_case": ignore_case,
        }
        # Filter out None values before passing to run_report
        params = {k: v for k, v in params.items() if v is not None}

        print(f"DEBUG: Running report={report_name} with params={params}", file=sys.stderr)

        try:

            egeria_client: EgeriaTech = GLOBAL_EGERIA_CLIENT
            print("DEBUG: Egeria Client connected", file=sys.stderr)
            result = await asyncio.wait_for(
                _async_run_report_tool(
                    report=report_name,
                    egeria_client=egeria_client,
                    params=params),
                timeout=30  # Adjust timeout as needed
            )

            print("DEBUG: run_report completed successfully", file=sys.stderr)
            return _ok(result)
        except Exception as e:
            # Re-raise the exception to be sent back as a JSON-RPC error
            print(f"DEBUG: Exception occurred: {str(e)}", file=sys.stderr)
            raise

    @srv.tool(name="prompt")
    async def natural_language_prompt(prompt: str) -> Dict[str, Any]:
        """
        Handles natural language queries from the user.
        In a production environment, this would call an LLM API.
        """
        print(f"DEBUG: Received natural language prompt: {prompt}", file=sys.stderr)

        # Example of simple logic: If the user asks to list reports, delegate to the tool.
        if "list" in prompt.lower() and "reports" in prompt.lower():
            print("DEBUG: Delegating prompt to list_reports tool.", file=sys.stderr)
            return list_reports()  # This is sync, so no await needed
        elif "run" in prompt.lower() and "report" in prompt.lower():
            print("DEBUG: Delegating prompt to run_report tool.", file=sys.stderr)

            match = re.search(r'report\s+([a-zA-Z0-9]+)', prompt, re.IGNORECASE)
            report_name = match.group(1) if match else None

            if report_name:
                print(f"DEBUG: Extracted report name: {report_name}", file=sys.stderr)

                page_size_match = re.search(r'page size of\s+(\d+)', prompt, re.IGNORECASE)
                page_size = int(page_size_match.group(1)) if page_size_match else None

                search_match = re.search(r'search for\s+(.*?)(?:\s+in\s+report|\.|$)', prompt, re.IGNORECASE)

                if search_match:
                    search_string = search_match.group(1).strip()

                    if search_string:
                        print(
                            f"DEBUG: Delegating prompt to run_report tool. Report: {report_name}, Search: '{search_string}'",
                            file=sys.stderr)

                        # AWAIT the async function call
                        return await run_report_tool(
                            report_name=report_name,
                            page_size=page_size,
                            search_string=search_string
                        )

                # AWAIT the async function call
                return await run_report_tool(
                    report_name=report_name,
                    page_size=page_size
                )

        return {
            "response": f"Acknowledged natural language query: '{prompt}'. This would be sent to an LLM."
        }

    # CRITICAL: This is the missing step. It tells the server to read and process
    # JSON-RPC messages from standard input (stdin).
    srv.run()
    print("MCP server finished running.", file=sys.stderr)


if __name__ == "__main__":
    main()
