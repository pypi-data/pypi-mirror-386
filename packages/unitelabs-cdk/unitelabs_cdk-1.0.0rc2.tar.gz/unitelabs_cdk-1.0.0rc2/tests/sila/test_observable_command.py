import typing
import unittest.mock

import pytest

import sila
from sila.framework.errors.defined_execution_error import DefinedExecutionError
from unitelabs.cdk.sila.command.observable_command import ObservableCommand
from unitelabs.cdk.sila.commands.responses import Response
from unitelabs.cdk.sila.common.feature import Feature


class DefinedError(Exception):
    pass


@pytest.fixture
def feature():
    return Feature(identifier="Feature", name="Feature")


@pytest.fixture
def handler():
    return ObservableCommand(identifier="ObservableCommand", name="Unobservable Command", errors=[DefinedError])


class TestAttach:
    async def test_should_attach_handler(self, feature: Feature, handler: ObservableCommand):
        # Attach
        attached = handler.attach(feature)

        # Assert that the method returns the correct value
        assert attached is True
        assert feature.commands[handler._identifier] == handler._handler

    async def test_should_ignore_disabled_handler(self, feature: Feature, handler: ObservableCommand):
        # Attach
        handler._enabled = False
        attached = handler.attach(feature)

        # Assert that the method returns the correct value
        assert attached is False
        assert handler._identifier not in feature.commands

    async def test_should_call_enabled_callback(self, feature: Feature, handler: ObservableCommand):
        # Attach
        handler._enabled = unittest.mock.Mock(return_value=True)
        attached = handler.attach(feature)

        # Assert that the method returns the correct value
        assert attached is True
        assert feature.commands[handler._identifier] == handler._handler
        handler._enabled.assert_called_once_with(feature)

    async def test_should_attach_return_annotation(self, feature: Feature, handler: ObservableCommand):
        # Create handler
        def function() -> int:
            return unittest.mock.sentinel.response

        handler(function)

        # Attach
        with pytest.warns(match="No name found for Responses 0"):
            handler.attach(feature)

        # Assert that the method returns the correct value
        assert isinstance(handler._handler, sila.ObservableCommand)
        assert handler._handler.responses == {
            "Unnamed0": sila.Element(
                identifier="Unnamed0", display_name="Unnamed 0", description="", data_type=sila.Integer
            )
        }

    async def test_should_attach_missing_return_annotation(self, feature: Feature, handler: ObservableCommand):
        # Create handler
        def function():
            return unittest.mock.sentinel.response

        handler(function)

        # Attach
        handler.attach(feature)

        # Assert that the method returns the correct value
        assert isinstance(handler._handler, sila.ObservableCommand)
        assert handler._handler.responses == {}

    async def test_should_attach_annotated_return(self, feature: Feature, handler: ObservableCommand):
        # Create handler
        def function() -> typing.Annotated[int, sila.Unit("s", [sila.UnitComponent("Second")])]:
            return unittest.mock.sentinel.response

        handler(function)

        # Attach
        with pytest.warns(match="No name found for Responses 0"):
            handler.attach(feature)

        # Assert that the method returns the correct value
        assert isinstance(handler._handler, sila.ObservableCommand)
        assert issubclass(handler._handler.responses["Unnamed0"].data_type, sila.Constrained)
        assert handler._handler.responses["Unnamed0"].data_type.data_type == sila.Integer
        assert handler._handler.responses["Unnamed0"].data_type.constraints == [
            sila.Unit("s", [sila.UnitComponent("Second")])
        ]


class TestExecute:
    # Execute synchronous function with default parameters.
    async def test_execute_synchronous_default_parameters(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        callback = unittest.mock.Mock()

        @Response("Response")
        def function() -> str:
            callback()
            return unittest.mock.sentinel.response

        handler(function)
        handler.attach(feature)

        # Execute function
        result = await handler.execute(metadata={})

        # Assert that the function was called with the correct arguments
        callback.assert_called_once_with()

        # Assert that the method returns the correct value
        assert result == {"Response": unittest.mock.sentinel.response}

    # Execute synchronous function with custom parameters.
    async def test_execute_synchronous_custom_parameters(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        callback = unittest.mock.Mock()

        @Response("Response")
        def function(argument: str) -> str:
            callback(argument=argument)

            return unittest.mock.sentinel.response

        handler(function)
        handler.attach(feature)

        # Execute function
        result = await handler.execute(metadata={}, argument="World, World!")

        # Assert that the function was called with the correct arguments
        callback.assert_called_once_with(argument="World, World!")

        # Assert that the method returns the correct value
        assert result == {"Response": unittest.mock.sentinel.response}

    # Execute synchronous function with no return value.
    async def test_execute_synchronous_returns_none(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        callback = unittest.mock.Mock()

        def function(argument: str):
            callback(argument=argument)

        handler(function)
        handler.attach(feature)

        # Execute function
        result = await handler.execute(metadata={}, argument="World, World!")

        # Assert that the method returns the correct value
        callback.assert_called_once_with(argument="World, World!")
        assert result == {}

    # Verify that the method raises an error when the synchronous function raises.
    async def test_raises_when_synchronous_raises(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        def function():
            msg = "Hello, World!"
            raise Exception(msg)

        handler(function)
        handler.attach(feature)

        # Execute function
        with pytest.raises(Exception, match=r"Exception: Hello, World!"):
            await handler.execute(metadata={})

    # Verify that the method raises a defined execution error when the synchronous decorator knows the error type.
    async def test_raises_when_synchronous_raises_known_error(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        def function():
            msg = "Hello, World!"
            raise DefinedError(msg)

        handler(function)
        handler.attach(feature)

        # Execute function
        with pytest.raises(DefinedExecutionError) as exc_info:
            await handler.execute(metadata={})

        assert exc_info.value.identifier == "DefinedError"
        assert exc_info.value.display_name == "Defined Error"
        assert exc_info.value.description == "Common base class for all non-exit exceptions."
        assert exc_info.value.message == "Hello, World!"

    # Execute asynchronous function with default parameters.
    async def test_execute_asynchronous_default_parameters(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        callback = unittest.mock.AsyncMock()

        @Response("Response")
        async def function() -> str:
            await callback()
            return unittest.mock.sentinel.response

        handler(function)
        handler.attach(feature)

        # Execute function
        result = await handler.execute(function=function, metadata={})

        # Assert that the function was called with the correct arguments
        callback.assert_awaited_once_with()

        # Assert that the method returns the correct value
        assert result == {"Response": unittest.mock.sentinel.response}

    # Execute asynchronous function with custom parameters.
    async def test_execute_asynchronous_custom_parameters(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        callback = unittest.mock.AsyncMock()

        @Response("Response")
        async def function(argument: str) -> str:
            await callback(argument=argument)

            return unittest.mock.sentinel.response

        handler(function)
        handler.attach(feature)

        # Execute function
        result = await handler.execute(metadata={}, argument="World, World!")

        # Assert that the function was called with the correct arguments
        callback.assert_awaited_once_with(argument="World, World!")

        # Assert that the method returns the correct value
        assert result == {"Response": unittest.mock.sentinel.response}

    # Execute asynchronous function with no return value.
    async def test_execute_asynchronous_returns_none(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        callback = unittest.mock.AsyncMock()

        async def function(argument: str):
            await callback(argument=argument)

        handler(function)
        handler.attach(feature)

        # Execute function
        result = await handler.execute(metadata={}, argument="World, World!")

        # Assert that the method returns the correct value
        callback.assert_awaited_once_with(argument="World, World!")
        assert result == {}

    # Verify that the method raises an error when the asynchronous function raises.
    async def test_raises_when_asynchronous_raises(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        async def function():
            msg = "Hello, World!"
            raise Exception(msg)

        handler(function)
        handler.attach(feature)

        # Execute function
        with pytest.raises(Exception, match=r"Exception: Hello, World!"):
            await handler.execute(metadata={})

    # Verify that the method raises a defined execution error when the asynchronous decorator knows the error type.
    async def test_raises_when_asynchronous_raises_known_error(self, feature: Feature, handler: ObservableCommand):
        # Initialize the observable command
        async def function():
            msg = "Hello, World!"
            raise DefinedError(msg)

        handler(function)
        handler.attach(feature)

        # Execute function
        with pytest.raises(DefinedExecutionError) as exc_info:
            await handler.execute(metadata={})

        assert exc_info.value.identifier == "DefinedError"
        assert exc_info.value.display_name == "Defined Error"
        assert exc_info.value.description == "Common base class for all non-exit exceptions."
        assert exc_info.value.message == "Hello, World!"
