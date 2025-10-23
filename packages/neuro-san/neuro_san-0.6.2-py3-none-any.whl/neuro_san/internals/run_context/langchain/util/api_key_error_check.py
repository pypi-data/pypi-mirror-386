
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from typing import Dict
from typing import List

# Dictionary with provider key env var -> strings to look for
API_KEY_EXCEPTIONS: Dict[str, List] = {
    "OPENAI_API_KEY": ["OPENAI_API_KEY", "Incorrect API key provided"],
    "ANTHROPIC_API_KEY": ["ANTHROPIC_API_KEY", "anthropic_api_key", "invalid x-api-key", "credit balance"],
    "GOOGLE_API_KEY": ["Application Default Credentials", "default credentials", "Gemini: 400 API key not valid"],

    # Azure OpenAI requires several parameters; all can be set via environment variables
    # except "deployment_name", which must be provided explicitly.
    "AZURE_OPENAI_API_KEY": ["invalid subscription key", "wrong API endpoint"],
    "AZURE_OPENAI_ENDPOINT": ["base_url", "azure_endpoint", "AZURE_OPENAI_ENDPOINT"],
    "OPENAI_API_VERSION": ["api_version", "OPENAI_API_VERSION"],
    "AZURE_OPENAI_DEPLOYMENT_NAME": ["API deployment for this resource does not exist"],
}

AZURE_DOCUMENTATION: str = "https://learn.microsoft.com/en-us/azure/ai-services/openai/"
"chatgpt-quickstart?tabs=keyless%2Ctypescript-keyless%2Cpython-new%2Ccommand-line&pivots=programming-language-python"

# Dictionary with provider key env var -> link to documentation
API_KEY_DOCUMENTATION: Dict[str, List] = {
    "AZURE_OPENAI_API_KEY": AZURE_DOCUMENTATION,
    "AZURE_OPENAI_ENDPOINT": AZURE_DOCUMENTATION,
    "OPENAI_API_VERSION": AZURE_DOCUMENTATION,
    "AZURE_OPENAI_DEPLOYMENT_NAME": AZURE_DOCUMENTATION,
}

INTERNAL_ERRORS_LIST: List[str] = ["bound to a different event loop"]


class ApiKeyErrorCheck:
    """
    Class for common policy when checking for API key errors for various LLM providers.
    """

    @staticmethod
    def check_for_api_key_exception(exception: Exception) -> str:
        """
        :param exception: An exception to check
        :return: A more helpful exception message if it relates to an API key or None
                if it does not pertain to an API key.
        """

        exception_message: str = str(exception)
        matched_keys: List[str] = []
        matched_documentation_link: str = ""

        # Collect all keys that have any associated string in the exception message
        # since there could be multiple keys with the exact same message.
        for api_key, string_list in API_KEY_EXCEPTIONS.items():
            for find_string in string_list:
                if find_string in exception_message:
                    matched_keys.append(api_key)
                    matched_documentation_link = API_KEY_DOCUMENTATION.get(api_key, "")
                    # No need to check the remaining strings for this key
                    break

        if matched_keys:
            keys_str = ", ".join(matched_keys)
            return f"""
A value for the {keys_str} environment variable must be correctly set in the neuro-san
server or run-time enviroment in order to use this agent network.

Some things to try:
1) Double check that your value for {keys_str} is set correctly
2) If you do not have a value for {keys_str}, visit the LLM provider's website to get one {matched_documentation_link}
3) It's possible that your credit balance on your account with the LLM provider is too low
   to make the request.  Check that.
4) Sometimes these errors happen because of firewall blockages to the site that hosts the LLM.
   Try checking that you can reach the regular UI for the LLM from a web browser
   on the same machine making this request.
"""

        return None

    @staticmethod
    def check_for_internal_error(exception_traceback: str) -> bool:
        """
        Check if exception traceback points to some internal LLM stack problem,
        not necessarily related to API keys being absent or invalid.
        This function used as an additional check while using check_for_api_key_exception()
        :param exception_traceback: exception traceback string;
        :return: True if exception seems to be caused by some internal problems,
                 False otherwise
        """
        for err_msg in INTERNAL_ERRORS_LIST:
            if err_msg in exception_traceback:
                return True
        return False
