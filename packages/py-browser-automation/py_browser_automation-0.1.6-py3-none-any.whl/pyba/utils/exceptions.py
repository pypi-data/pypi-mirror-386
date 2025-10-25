class PromptNotPresent(Exception):
    """
    This exception is raised when the user forgets to enter a prompt to the engine
    """

    def __init__(self):
        super().__init__("Please provide a prompt for us to work on")


class ServiceNotSelected(Exception):
    """
    This exception is raised when the user doesn't set an API key in the engine
    """

    def __init__(self):
        super().__init__("Please set either a VertexAI project ID or an OpenAI key")


class ServerLocationUndefined(Exception):
    """
    This exception is raised when the user doesn't define the server location
    for a VertexAI project.
    """

    def __init__(self, server_location):
        super().__init__(
            f"The server location {server_location} is undefined. Please visit https://cloud.google.com/vertex-ai/docs/general/locations and choose a location that your credits are tied to."
        )


class CredentialsnotSpecified(Exception):
    """
    Exception raised in the login scripts when the relevant credentials haven't been specified
    """

    def __init__(self, site_name: str):
        super().__init__(f"Please specify all the credentials for the {site_name} engine.")


class UnknownSiteChosen(Exception):
    """
    Exception to be raised when the user chooses a site for automated login that isn't implemented yet.
    """

    def __init__(self, sites: list):
        super().__init__(
            f"Unknown site chosen for automated login. The following sites are available: {sites}"
        )
