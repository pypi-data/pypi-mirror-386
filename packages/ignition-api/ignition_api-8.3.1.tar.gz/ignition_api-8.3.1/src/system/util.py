"""Utility Functions.

The following functions give you access to view various Gateway and
Client data, as well as interact with other various systems.
"""

from __future__ import print_function

__all__ = [
    "APPLET_FLAG",
    "CLIENT_FLAG",
    "DESIGNER_FLAG",
    "FULLSCREEN_FLAG",
    "MOBILE_FLAG",
    "PREVIEW_FLAG",
    "SSL_FLAG",
    "WEBSTART_FLAG",
    "audit",
    "execute",
    "getGatewayStatus",
    "getGlobals",
    "getLogger",
    "getModules",
    "getProjectName",
    "getProperty",
    "getSessionInfo",
    "getVersion",
    "globals",
    "invokeAsynchronous",
    "jsonDecode",
    "jsonEncode",
    "modifyTranslation",
    "queryAuditLog",
    "sendMessage",
    "sendRequest",
    "sendRequestAsync",
    "setLoggingLevel",
    "threadDump",
    "translate",
]

import getpass
import json
import os
import platform
from typing import Any, Callable, Dict, Iterable, List, Optional

import system.__version__ as version
from com.inductiveautomation.ignition.common import BasicDataset
from com.inductiveautomation.ignition.common.model import Version
from com.inductiveautomation.ignition.common.script.builtin import (
    DatasetUtilities,
    SystemUtilities,
)
from com.inductiveautomation.ignition.common.util import LoggerEx
from dev.coatl.helper.types import AnyStr
from java.lang import Thread
from java.util import Date

APPLET_FLAG = 16
CLIENT_FLAG = 4
DESIGNER_FLAG = 1
FULLSCREEN_FLAG = 32
MOBILE_FLAG = 128
PREVIEW_FLAG = 2
SSL_FLAG = 64
WEBSTART_FLAG = 8


globals = {}  # type: Dict[AnyStr, Any]


def audit(
    action=None,  # type: Optional[AnyStr]
    actionValue=None,  # type: Optional[AnyStr]
    auditProfile="",  # type: AnyStr
    actor=None,  # type: Optional[AnyStr]
    actorHost="localhost",  # type: AnyStr
    originatingSystem=None,  # type: Optional[List[AnyStr]]
    eventTimestamp=None,  # type: Optional[Date]
    originatingContext=4,  # type: int
    statusCode=0,  # type: int
):
    # type: (...) -> None
    """Inserts a record into an audit profile.

    Args:
        action: What happened. Default is null. Optional.
        actionValue: What the action happened to. Default is null.
            Optional.
        auditProfile: Where the audit record should be stored. Defaults
            to the project's audit profile (if specified), or the
            gateway audit profile if calling in the gateway or
            perspective scope. Optional.
        actor: Who made the change. Will be populated automatically if
            omitted, assuming there is a known user. Optional.
        actorHost: The hostname of whoever made the change. Will be
            populated automatically if omitted.
        originatingSystem: An even-length list providing additional
            context to the audit event. Optional.
        eventTimestamp: When the event happened. Will be set to the
            current time if omitted. Optional.
        originatingContext: What scope the event originated from: 1
            means Gateway, 2 means Designer, 4 means Client. Will be set
            automatically if omitted. Optional.
        statusCode: A quality code to attach to the object. Defaults to
            0, indicating no special meaning. Optional.
    """
    print(
        action,
        actionValue,
        auditProfile,
        actor,
        actorHost,
        originatingSystem,
        eventTimestamp,
        originatingContext,
        statusCode,
    )


def execute(commands):
    # type: (List[AnyStr]) -> None
    """Executes the given commands via the operating system, in a
    separate process.

    The commands argument is an array of strings. The first string is
    the program to execute, with subsequent strings being the arguments
    to that command.

    Args:
        commands: A list containing the command (1st entry) and
            associated arguments (remaining entries) to execute.
    """
    print(commands)


def getGatewayStatus(
    gatewayAddress,  # type: AnyStr
    connectTimeoutMillis=None,  # type: Optional[int]
    socketTimeoutMillis=None,  # type: Optional[int]
    bypassCertValidation=True,  # type: bool
):
    # type: (...) -> unicode
    """Returns a string that indicates the status of the Gateway.

    A status of RUNNING means that the Gateway is fully functional.
    Thrown exceptions return "ERROR" with the error message appended to
    the string.

    Args:
        gatewayAddress: The gateway address to ping, in the form of
            ADDR:PORT/main.
        connectTimeoutMillis: The maximum time in milliseconds to
            attempt to initially contact a Gateway. Optional.
        socketTimeoutMillis: The maximum time in milliseconds to wait
            for a response from a Gateway after initial connection has
            been established. Optional.
        bypassCertValidation: f the target address is an HTTPS address,
            and this parameter is True, the system will bypass all SSL
            certificate validation. This is not recommended, though is
            sometimes necessary for self-signed certificates. Optional.

    Returns:
        A string that indicates the status of the Gateway. A status of
        RUNNING means that the Gateway is fully functional.
    """
    print(
        gatewayAddress, connectTimeoutMillis, socketTimeoutMillis, bypassCertValidation
    )
    return unicode("RUNNING")


def getGlobals():
    # type: () -> Dict[AnyStr, Any]
    """This method returns a dictionary that provides access to the
    legacy global namespace.

    As of version 7.7.0, most new scripts use the modern style of
    scoping, which makes the 'global' keyword act very differently. Most
    importantly, the modern scoping rules mean that variables declared
    as 'global' are only global within that one module. The
    system.util.getGlobals() method can be used to interact with older
    scripts that used the old meaning of the 'global' keyword.

    The globals dictionary will now persist across the lifetime of the
    JVM, and it's now accessible at system.util.globals.

    Returns:
        The global namespace, as a dictionary.
    """
    return globals


def getLogger(name):
    # type: (AnyStr) -> LoggerEx
    """Returns a Logger object that can be used to log messages to the
    console.

    Args:
        name: The name of a logger to create.

    Returns:
        A new LoggerEx object used to log informational and error
        messages.
    """
    print(name)
    return LoggerEx()


def getModules():
    # type: () -> BasicDataset
    """Returns a dataset of information about each installed module.
    Each row represents a single module.

    Returns:
        A dataset, where each row represents a module. Contains five
        columns: Id, Name, Version, State (Running, Faulted, etc), and
        its current License Status (Trial, Activated, etc.).
    """
    return BasicDataset()


def getProjectName():
    # type: () -> AnyStr
    """Returns the name of the project that is currently being run.

    Returns:
        The name of the currently running project.
    """
    return "MyProject"


def getProperty(propertyName):
    # type: (AnyStr) -> Optional[unicode]
    r"""Retrieves the value of a named system property.

    Some of the available properties are:

        file.separator. The system file separator character, for
            example, "/" (unix) or "\" (windows).
        line.separator. The system line separator string, for example,
            "\r\n" (carriage return, newline).
        os.arch. Operating system architecture, for example, "x86".
        os.name. Operating system name, for example, "Windows XP".
        os.version. Operating system version, for example, "5.1".
        user.home. User's home directory.
        user.name. User's account name.

    Args:
        propertyName: The name of the system property to get.

    Returns:
        The value for the named property.
    """
    ret = None

    if propertyName == "file.separator":
        ret = os.sep
    elif propertyName == "line.separator":
        ret = os.linesep
    elif propertyName == "os.arch":
        ret = platform.machine()
    elif propertyName == "os.name":
        ret = platform.system()
    elif propertyName == "os.version":
        ret = platform.release()
    elif propertyName == "user.home":
        ret = os.path.expanduser("~")
    elif propertyName == "user.name":
        ret = getpass.getuser()

    return unicode(ret)


def getSessionInfo(
    usernameFilter=None,  # type: Optional[AnyStr]
    projectFilter=None,  # type: Optional[AnyStr]
):
    # type: (...) -> DatasetUtilities.PyDataSet
    """Returns a PyDataSet holding information about all of the open
    Designer Sessions and Vision Clients.

    Optional regular-expression based filters can be provided to filter
    the username or the username and the project returned.

    Args:
        usernameFilter: A regular-expression based filter string to
            restrict the list by username. Optional.
        projectFilter: A regular-expression based filter string to
            restrict the list by project. Optional.

    Returns:
        A dataset representing the Gateway's current sessions.
    """
    print(usernameFilter, projectFilter)
    return DatasetUtilities.PyDataSet()


def getVersion():
    # type: () -> Version
    """Returns the Ignition version number that is currently being run.

    Returns:
        The currently running Ignition version number, as a Version
        object.
    """
    major, minor, rev = tuple(map(int, version.__version__.split(".")[:3]))
    build = int(version.__build__)
    return Version(major=major, minor=minor, rev=rev, build=build)


def invokeAsynchronous(
    function,  # type: Callable[..., Any]
    args=None,  # type: Optional[Iterable[Any]]
    kwargs=None,  # type: Optional[Dict[AnyStr, Any]]
    description=None,  # type: Optional[AnyStr]
):
    # type: (...) -> Thread
    """Invokes (calls) the given Python function on a different thread.

    This means that calls to invokeAsynchronous will return immediately,
    and then the given function will start executing asynchronously on a
    different thread. This is useful for long-running data intensive
    functions, where running them synchronously (in the GUI thread)
    would make the GUI non-responsive for an unacceptable amount of
    time.

    Args:
        function: A Python function object that will get invoked with no
            arguments in a separate thread.
        args: A list or tuple of Python objects that will be provided to
            the called function as arguments. Equivalent to the *
            operator. Optional.
        kwargs: A dictionary of keyword argument names to Python object
            values that will be provided to the called function as
            keyword arguments. Equivalent to the ** operator. Optional.
        description: A description to use for the asynchronous thread.
            Will be displayed on the current scope's diagnostic view for
            scripts. For Vision and the Designer, this would be the
            "Scripts" tab of the Diagnostics popup. For Perspective and
            the Gateway scope, this would be the Gateway's Running
            Scripts status page. Optional.

    Returns:
        The executing thread.
    """
    print(function, args, kwargs, description)
    return Thread()


def jsonDecode(jsonString):
    # type: (AnyStr) -> Any
    """Takes a JSON string and converts it into a Python object such as
    a list or a dictionary.

    If the input is not valid json, a string is returned.

    Args:
        jsonString: The JSON string to decode into a Python object.

    Returns:
        The decoded Python object.
    """
    return json.loads(jsonString)


def jsonEncode(pyObj, indentFactor=4):
    # type: (Iterable[Any], int) -> AnyStr
    """Takes a Python object such as a list or dict and converts into a
    JSON string.

    Args:
        pyObj: The Python object to encode into JSON such as a Python
            list or dictionary.
        indentFactor: The number of spaces to add to each level of
            indentation for prettyprinting. Optional.

    Returns:
        The encoded JSON string.
    """
    return json.dumps(pyObj, indent=indentFactor)


def modifyTranslation(term, translation, locale="es_MX"):
    # type: (AnyStr, AnyStr, AnyStr) -> None
    """This function allows you to add or modify a global translation.

    Args:
        term: The key term to translate.
        translation: The translated value to store.
        locale: If specified, the locale code (such as "es") identifying
            the language of the translation. If omitted, the function
            will attempt to detect the locale automatically. Optional.
    """
    print(term, translation, locale)


def queryAuditLog(
    auditProfileName=None,  # type: Optional[AnyStr]
    startDate=None,  # type: Optional[Date]
    endDate=None,  # type: Optional[Date]
    actorFilter=None,  # type: Optional[AnyStr]
    actionFilter=None,  # type: Optional[AnyStr]
    targetFilter=None,  # type: Optional[AnyStr]
    valueFilter=None,  # type: Optional[AnyStr]
    systemFilter=None,  # type: Optional[AnyStr]
    contextFilter=None,  # type: Optional[int]
):
    # type: (...) -> BasicDataset
    """Queries an audit profile for audit history.

    Returns the results as a dataset.

    Args:
        auditProfileName: The name of the audit profile to pull the
            history from. Optional.
        startDate: The earliest audit event to return. If omitted, the
            current time - 8 hours will be used. Optional.
        endDate: The latest audit event to return. If omitted, the
            current time will be used. Optional.
        actorFilter: A filter string used to restrict the results by
            actor. Optional.
        actionFilter: A filter string used to restrict the results by
            action. Optional.
        targetFilter: A filter string used to restrict the results by
            target. Optional.
        valueFilter: A filter string used to restrict the results by
            value. Optional.
        systemFilter: A filter string used to restrict the results by
            system. Optional.
        contextFilter: A bitmask used to restrict the results by
            context. 0x01 = Gateway, 0x02 = Designer, 0x04 = Client.
            Optional.

    Returns:
        A dataset with the audit events from the specified profile that
        match the filter arguments.
    """
    print(
        auditProfileName,
        startDate,
        endDate,
        actorFilter,
        actionFilter,
        targetFilter,
        valueFilter,
        systemFilter,
        contextFilter,
    )
    return BasicDataset()


def sendMessage(
    project,  # type: AnyStr
    messageHandler,  # type: AnyStr
    payload=None,  # type: Optional[Dict[AnyStr, Any]]
    scope=None,  # type: Optional[AnyStr]
    clientSessionId=None,  # type: Optional[AnyStr]
    user=None,  # type: Optional[AnyStr]
    hasRole=None,  # type: Optional[AnyStr]
    hostName=None,  # type: Optional[AnyStr]
    remoteServers=None,  # type: Optional[List[AnyStr]]
):
    # type: (...) -> List[AnyStr]
    """This function sends a message to clients running under the
    Gateway, or to a project within the Gateway itself.

    To handle received messages, you must set up event script message
    handlers within a project. These message handlers run Jython code
    when a message is received. You can add message handlers under the
    "Message" section of the client/Gateway event script configuration
    dialogs.

    Args:
        project: The name of the project containing the message handler.
        messageHandler: The name of the message handler that will fire
            upon receiving a message.
        payload: A dictionary which will get passed to the message
            handler. Use "payload" in the message handler to access
            dictionary variables. Optional.
        scope: Limits the scope of the message delivery to "C"
            (clients), "G" (Gateway), or "CG" for clients and the
            Gateway. Defaults to "C" if the user name, role or host name
            parameters are set, and to "CG" if none of these parameters
            are set. Optional.
        clientSessionId: Limits the message delivery to a client with
            the specified session ID. Optional.
        user: Limits the message delivery to clients where the specified
            user has logged in. Optional.
        hasRole: Limits the message delivery to any client where the
            logged in user has the specified user role. Optional.
        hostName: Limits the message delivery to the client that has the
            specified network host name. Optional.
        remoteServers: A list of Strings representing Gateway Server
            names. The message will be delivered to each server in the
            list. Upon delivery, the message is distributed to the local
            Gateway and clients as per the other parameters. Optional.

    Returns:
        A List of strings containing information about each system that
        was selected for delivery, where each List item is
        comma-delimited.
    """
    print(
        project,
        messageHandler,
        payload,
        scope,
        clientSessionId,
        user,
        hasRole,
        hostName,
        remoteServers,
    )
    return ["information about the system"]


def sendRequest(
    project,  # type: AnyStr
    messageHandler,  # type: AnyStr
    payload=None,  # type: Optional[Dict[AnyStr, Any]]
    hostName=None,  # type: Optional[AnyStr]
    remoteServer=None,  # type: Optional[AnyStr]
    timeoutSec=None,  # type: Optional[AnyStr]
):
    # type: (...) -> Any
    """This function sends a message to the Gateway, working in a
    similar manner to the sendMessage function, except sendRequest
    expects a response to the message.

    To handle received messages, you must set up Gateway Event Script
    message handlers within a project. These message handlers run Jython
    code when a message is received. You can then place a return at the
    end of the code to return something to where the sendRequest was
    originally called from. You can add message handlers under the
    "Message" section of the Gateway Event Script configuration dialog.

    Args:
        project: The name of the project containing the message handler.
        messageHandler: The name of the message handler that will fire
            upon receiving a message.
        payload: A PyDictionary which will get passed to the message
            handler. Use "payload" in the message handler to access
            dictionary variables. Optional.
        hostName: Limits the message delivery to the client that has the
            specified network host name. Optional.
        remoteServer: A string representing a target Gateway Server
            name. The message will be delivered to the remote Gateway
            over the Gateway Network. Upon delivery, the message is
            distributed to the local Gateway and clients as per the
            other parameters. Optional.
        timeoutSec: The number of seconds before the sendRequest call
            times out. Optional.

    Returns:
        The return from the message handler.
    """
    print(
        project,
        messageHandler,
        payload,
        hostName,
        remoteServer,
        timeoutSec,
    )
    return ""


def sendRequestAsync(
    project,  # type: AnyStr
    messageHandler,  # type: AnyStr
    payload=None,  # type: Optional[Dict[AnyStr, Any]]
    hostName=None,  # type: Optional[AnyStr]
    remoteServer=None,  # type: Optional[AnyStr]
    timeoutSec=None,  # type: Optional[int]
    onSuccess=None,  # type: Optional[Callable[..., Any]]
    onError=None,  # type: Optional[Callable[..., Any]]
):
    # type: (...) -> SystemUtilities.RequestImpl
    """This function sends a message to the Gateway and expects a
    response.

    Works in a similar manner to the sendRequest function, except
    sendRequestAsync will send the request and then immediately return a
    handle for it.

    Args:
        project: The name of the project containing the message handler.
        messageHandler: The name of the message handler that will fire
            upon receiving a message.
        payload: A PyDictionary which will get passed to the message
            handler. Use "payload" in the message handler to access
            dictionary variables. Optional.
        hostName: Limits the message delivery to the client that has the
            specified network host name. Optional.
        remoteServer: A string representing the target Gateway Server
            name. The message will be delivered to the remote Gateway
            over the Gateway Network. Upon delivery, the message is
            distributed to the local Gateway and clients as per the
            other parameters. Optional.
        timeoutSec: The number of seconds before the sendRequest call
            times out. Optional.
        onSuccess: Should take one argument, which will be the result
            from the message handler. Callback functions will be
            executed on the GUI thread, similar to
            system.util.invokeLater. Optional.
        onError: Should take one argument, which will be the exception
            encountered. Callback functions will be executed on the GUI
            thread, similar to system.util.invokeLater. Optional.

    Returns:
        The Request object that can be used while waiting for the
        message handler callback.
    """
    print(
        project,
        messageHandler,
        payload,
        hostName,
        remoteServer,
        timeoutSec,
        onSuccess,
        onError,
    )
    return SystemUtilities.RequestImpl(1000)


def setLoggingLevel(loggerName, loggerLevel):
    # type: (AnyStr, AnyStr) -> None
    """Sets the logging level on the given logger.

    This can be a logger you create, or a logger already defined in the
    system.

    Args:
        loggerName: The unique name of the logger to change the logging
            level on, for example "Tags.Client".
        loggerLevel: The level you want to change to logger to: "trace",
            "debug", "info", "warn" or "error".
    """
    print(loggerName, loggerLevel)


def threadDump():
    # type: () -> unicode
    """Creates a thread dump of the current running JVM.

    Returns:
        The dump of the current running JVM.
    """
    return unicode("""{0}\n  "version": "{1}"...{2}""").format(
        "{", getVersion().toParseableString(), "}"
    )


def translate(term, locale="es_MX", strict=False):
    # type: (AnyStr, Optional[AnyStr], Optional[bool]) -> AnyStr
    """This function allows you to retrieve the global translation of a
    term from the translation database using the current locale.

    Args:
        term: The term to look up.
        locale: Which locale to translate against. Useful when there are
            multiple locales defined for a single term. If omitted, the
            function attempts to use the current locale (as defined by
            the client, session, or Designer). Optional.
        strict: If False, the function will return the passed term
            (param 1) if it could not find a defined translation for the
            locale: meaning, if you pass a term that hasn't been
            configured, the function will just send the term back to
            you. If True, then the function will return a None when it
            fails to find a defined translation. Default is False.
            Optional.

    Returns:
        The translated term.
    """
    print(term, locale, strict)
    return term
