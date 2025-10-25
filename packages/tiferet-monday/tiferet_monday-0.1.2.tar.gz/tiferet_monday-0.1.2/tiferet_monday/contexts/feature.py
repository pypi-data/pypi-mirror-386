"""Tiferet Monday Feature Context"""

# *** imports

# ** core
from typing import Any, Callable
from time import sleep

# ** infra
from tiferet import Command, TiferetError
from tiferet.contexts import RequestContext, FeatureContext

# *** contexts

# * context: monday_feature_context
class MondayFeatureContext(FeatureContext):
    """
    Context for managing feature-related operations in Monday.com.
    """

    # * method: handle_retry

    # method: handle_retry
    def handle_retry(self,
        retry_in_seconds: int, 
        handler: Callable = lambda data: data
    ) -> Any:
        '''
        Handle retry logic based on the provided error information.

        :param error: The original error encountered.
        :type error: TiferetError
        :param monday_error: The specific error message from Monday.com.
        :type monday_error: str
        :param retry_in_seconds: The number of seconds to wait before retrying.
        :type retry_in_seconds: int
        '''
        
        # Wait for the specified number of seconds before retrying.
        sleep(retry_in_seconds)

        # Retry the command after waiting
        return handler()


    # * method: handle_command
    def handle_command(self,
        command: Command, 
        request: RequestContext,
        data_key: str = None,
        pass_on_error: bool = False,
        **kwargs
    ) -> Any:
        '''
        Handle the execution of a command with the provided request and command-handling options.

        :param command: The command to execute.
        :type command: Command
        :param request: The request context object.
        :type request: RequestContext
        :param debug: Debug flag.
        :type debug: bool
        :param data_key: Optional key to store the result in the request data.
        :type data_key: str
        :param pass_on_error: If True, pass on the error instead of raising it.
        :type pass_on_error: bool
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        '''

        # Call the superclass method to handle the command.
        try:
            return super().handle_command(
                command=command,
                request=request,
                data_key=data_key,
                pass_on_error=pass_on_error,
                **kwargs
            )
        
        # Catch TiferetError exceptions.
        except TiferetError as e:

            # Raise the exception for non-complexity budget exhausted errors.
            if not e.error_code == 'COMPLEXITY_BUDGET_EXHAUSTED':
                raise e
            
            # Handle complexity budget exhausted errors with retry.
            return self.handle_retry(
                e.args[1],
                handler=lambda: self.handle_command(
                    command=command,
                    request=request,
                    data_key=data_key,
                    pass_on_error=pass_on_error,
                    **kwargs
                )
            )
