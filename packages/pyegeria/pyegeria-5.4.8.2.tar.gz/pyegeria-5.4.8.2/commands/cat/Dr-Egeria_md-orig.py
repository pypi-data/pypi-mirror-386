"""
This is an ongoing experiment in parsing and playing with Freddie docs
"""
import json
import os
from rich import print
from rich.console import Console

from pyegeria.md_processing_utils import (commands,
                                          process_provenance_command)

import click
from pyegeria import (extract_command, process_glossary_upsert_command, process_term_upsert_command,
                      process_category_upsert_command,
                      get_current_datetime_string, process_per_proj_upsert_command, EgeriaTech
                      )
import commands
from datetime import datetime

EGERIA_METADATA_STORE = os.environ.get("EGERIA_METADATA_STORE", "active-metadata-store")
EGERIA_KAFKA_ENDPOINT = os.environ.get("KAFKA_ENDPOINT", "localhost:9092")
EGERIA_PLATFORM_URL = os.environ.get("EGERIA_PLATFORM_URL", "https://localhost:9443")
EGERIA_VIEW_SERVER = os.environ.get("EGERIA_VIEW_SERVER", "view-server")
EGERIA_VIEW_SERVER_URL = os.environ.get(
    "EGERIA_VIEW_SERVER_URL", "https://localhost:9443"
)
EGERIA_INTEGRATION_DAEMON = os.environ.get("EGERIA_INTEGRATION_DAEMON", "integration-daemon")
EGERIA_INTEGRATION_DAEMON_URL = os.environ.get(
    "EGERIA_INTEGRATION_DAEMON_URL", "https://localhost:9443"
)
EGERIA_ADMIN_USER = os.environ.get("ADMIN_USER", "garygeeke")
EGERIA_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "secret")
EGERIA_USER = os.environ.get("EGERIA_USER", "erinoverview")
EGERIA_USER_PASSWORD = os.environ.get("EGERIA_USER_PASSWORD", "secret")
EGERIA_WIDTH = os.environ.get("EGERIA_WIDTH", 220)
EGERIA_JUPYTER = os.environ.get("EGERIA_JUPYTER", False)
EGERIA_HOME_GLOSSARY_GUID = os.environ.get("EGERIA_HOME_GLOSSARY_GUID", None)
EGERIA_GLOSSARY_PATH = os.environ.get("EGERIA_GLOSSARY_PATH", None)
EGERIA_ROOT_PATH = os.environ.get("EGERIA_ROOT_PATH", "../../")
EGERIA_INBOX_PATH = os.environ.get("EGERIA_INBOX_PATH", "md_processing/dr_egeria_inbox")
EGERIA_OUTBOX_PATH = os.environ.get("EGERIA_OUTBOX_PATH", "md_processing/dr_egeria_outbox")

console = Console(width=int(EGERIA_WIDTH))



@click.command("process-markdown-file", help="Process a markdown file and return the output as a string.")
@click.option("--file-path", help="File path to markdown file",
              default="glossary_test1.md")
@click.option("--directive", default="display-only", help="How to process the file")
@click.option("--server", default=EGERIA_VIEW_SERVER, help="Egeria view server to use.")
@click.option(
    "--url", default=EGERIA_VIEW_SERVER_URL, help="URL of Egeria platform to connect to"
)
@click.option("--userid", default=EGERIA_USER, help="Egeria user")
@click.option("--user_pass", default=EGERIA_USER_PASSWORD, help="Egeria user password")
def process_markdown_file(
        file_path: str,
        directive: str,
        server: str,
        url: str,
        userid: str,
        user_pass: str,
        ):

    client = EgeriaTech(server, url, user_id=userid)
    token = client.create_egeria_bearer_token(userid, user_pass)

    updated = False
    full_file_path = os.path.join(EGERIA_ROOT_PATH, EGERIA_INBOX_PATH, file_path)
    print(f"Processing Markdown File: {full_file_path}")
    try:
        with open(full_file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found at path: {full_file_path}")
        return {}  # Return empty dict if file not found

    final_output =""
    prov_output = (f"\n* Results from processing file {file_path} on "
                    f"{datetime.now().strftime("%Y-%m-%d %H:%M")}\n")
    h1_blocks = []
    current_block = ""
    in_h1_block = False
    element_dictionary = {}

    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespace

        if line.startswith("# ") and not in_h1_block:  # Start of a new H1 block
            if current_block:
                h1_blocks.append(current_block)
            current_block = line
            in_h1_block = True
        elif line.startswith("---") and in_h1_block:  # End of the current H1 block
            h1_blocks.append(current_block)
            current_block = ""
            in_h1_block = False
        elif in_h1_block:  # Add line to the current H1 block
            current_block += "\n" + line
        else:
            # Add non-H1 blocks directly to the final output
            final_output += line

    if current_block:  # Add the last H1 block
        h1_blocks.append(current_block)
    prov_found = False
    # Process each identified H1 block
    for block in h1_blocks:
        potential_command = extract_command(block)  # Extract potential object_action

        if potential_command in commands:
            # Process the block based on the object_action
            if potential_command == "Provenance":
                prov_found = True
                result = process_provenance_command(file_path, block)
            elif potential_command in ["Create Glossary", "Update Glossary"]:
                result = process_glossary_upsert_command(client, block, directive)
            elif potential_command in ["Create Category", "Update Category"]:
                result = process_category_upsert_command(client, block, directive)
            elif potential_command in ["Create Term", "Update Term"]:
                result = process_term_upsert_command(client, block, directive)
            elif potential_command in ["Create Personal Project", "Update Personal Project"]:
                result = process_per_proj_upsert_command(client, block, directive)
            else:
                # If object_action is not recognized, copy the block as-is
                result = None

            if result:
                if directive == "process":
                    updated = True
                    final_output += f"\n---\n{result}\n"
                    print(json.dumps(element_dictionary, indent=4))
            elif directive == "process":
                # Handle case with errors (skip this block but notify the user)
                print(f"\n==>\tErrors found while processing command: \'{potential_command}\'\n"
                      f"\tPlease correct and try again. \n")
                final_output += f"\n---\n{block}\n"
        else:
            # If no object_action is detected, add the block to the final output as-is
            final_output += f"\n---\n{block}\n"


    # Write the final_output to a new file if updated
    try:
        if updated:
            path, filename = os.path.split(file_path)  # Get both parts
            new_filename = f"processed-{get_current_datetime_string()}-{filename}"  # Create the new filename
            new_file_path = os.path.join(EGERIA_ROOT_PATH, EGERIA_OUTBOX_PATH, new_filename)  # Construct the new path
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)

            with open(new_file_path, 'w') as f2:
                f2.write(final_output)
                if not prov_found:
                    prov_output += f"\n# Provenance:\n{prov_output}\n"
                f2.write(prov_output)
            click.echo(f"\n==> Notebook written to {new_file_path}")
        else:
            click.echo("\nNo updates detected. New File not created.")

    except (Exception):
        console.print_exception(show_locals=True)


if __name__ == "__main__":
    process_markdown_file()
