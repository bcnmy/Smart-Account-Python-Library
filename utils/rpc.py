import requests
import time
import json
from typing import Union


class RPC:
    """
    A base class to interact with an RPC endpoint.

    Attributes:
        rpc_url (str): The URL of the RPC endpoint.
    """

    def __init__(self, rpc_url: str):
        """
        Initializes the RPC instance.

        Args:
            rpc_url (str): The URL of the RPC endpoint.
        """
        self.rpc_url = rpc_url

    def _send_json_rpc_request(
        self, method: str, params: list
    ) -> Union[dict, str, None]:
        """
        Sends a JSON-RPC request to the RPC endpoint.

        Args:
            method (str): The JSON-RPC method to be called.
            params (list): The parameters for the JSON-RPC method.

        Returns:
            Union[dict, str]: The result from the JSON-RPC call.

        Raises:
            Exception: If the request was not successful.
        """
        # Create the JSON-RPC request payload
        payload = {
            "method": method,
            "params": params,
            "id": int(time.time()),
            "jsonrpc": "2.0",
        }

        # Make the request to the RPC endpoint
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            self.rpc_url, headers=headers, data=json.dumps(payload)
        )

        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            if "result" in response_json:
                return response_json["result"]
            elif "error" in response_json:
                return response_json["error"]
            else:
                return response_json
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
