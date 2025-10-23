from typing import Any, Callable, Dict, Iterable, List, Optional

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

APPLET_FLAG: int
CLIENT_FLAG: int
DESIGNER_FLAG: int
FULLSCREEN_FLAG: int
MOBILE_FLAG: int
PREVIEW_FLAG: int
SSL_FLAG: int
WEBSTART_FLAG: int
globals: Dict[AnyStr, Any]

def audit(
    action: Optional[AnyStr] = ...,
    actionValue: Optional[AnyStr] = ...,
    auditProfile: AnyStr = ...,
    actor: Optional[AnyStr] = ...,
    actorHost: AnyStr = ...,
    originatingSystem: Optional[List[AnyStr]] = ...,
    eventTimestamp: Optional[Date] = ...,
    originatingContext: int = ...,
    statusCode: int = ...,
) -> None: ...
def execute(commands: List[AnyStr]) -> None: ...
def getGatewayStatus(
    gatewayAddress: AnyStr,
    connectTimeoutMillis: Optional[int] = ...,
    socketTimeoutMillis: Optional[int] = ...,
    bypassCertValidation: bool = ...,
) -> unicode: ...
def getGlobals() -> Dict[AnyStr, Any]: ...
def getLogger(name: AnyStr) -> LoggerEx: ...
def getModules() -> BasicDataset: ...
def getProjectName() -> AnyStr: ...
def getProperty(propertyName: AnyStr) -> Optional[unicode]: ...
def getSessionInfo(
    usernameFilter: Optional[AnyStr] = ..., projectFilter: Optional[AnyStr] = ...
) -> DatasetUtilities.PyDataSet: ...
def getVersion() -> Version: ...
def invokeAsynchronous(
    function: Callable[..., Any],
    args: Optional[Iterable[Any]] = ...,
    kwargs: Optional[Dict[AnyStr, Any]] = ...,
    description: Optional[AnyStr] = ...,
) -> Thread: ...
def jsonDecode(jsonString: AnyStr) -> Any: ...
def jsonEncode(pyObj: Iterable[Any], indentFactor: int = ...) -> AnyStr: ...
def modifyTranslation(
    term: AnyStr, translation: AnyStr, locale: AnyStr = ...
) -> None: ...
def queryAuditLog(
    auditProfileName: Optional[AnyStr] = ...,
    startDate: Optional[Date] = ...,
    endDate: Optional[Date] = ...,
    actorFilter: Optional[AnyStr] = ...,
    actionFilter: Optional[AnyStr] = ...,
    targetFilter: Optional[AnyStr] = ...,
    valueFilter: Optional[AnyStr] = ...,
    systemFilter: Optional[AnyStr] = ...,
    contextFilter: Optional[int] = ...,
) -> BasicDataset: ...
def sendMessage(
    project: AnyStr,
    messageHandler: AnyStr,
    payload: Optional[Dict[AnyStr, Any]] = ...,
    scope: Optional[AnyStr] = ...,
    clientSessionId: Optional[AnyStr] = ...,
    user: Optional[AnyStr] = ...,
    hasRole: Optional[AnyStr] = ...,
    hostName: Optional[AnyStr] = ...,
    remoteServers: Optional[List[AnyStr]] = ...,
) -> List[AnyStr]: ...
def sendRequest(
    project: AnyStr,
    messageHandler: AnyStr,
    payload: Optional[Dict[AnyStr, Any]] = ...,
    hostName: Optional[AnyStr] = ...,
    remoteServer: Optional[AnyStr] = ...,
    timeoutSec: Optional[AnyStr] = ...,
) -> Any: ...
def sendRequestAsync(
    project: AnyStr,
    messageHandler: AnyStr,
    payload: Optional[Dict[AnyStr, Any]] = ...,
    hostName: Optional[AnyStr] = ...,
    remoteServer: Optional[AnyStr] = ...,
    timeoutSec: Optional[int] = ...,
    onSuccess: Optional[Callable[..., Any]] = ...,
    onError: Optional[Callable[..., Any]] = ...,
) -> SystemUtilities.RequestImpl: ...
def setLoggingLevel(loggerName: AnyStr, loggerLevel: AnyStr) -> None: ...
def threadDump() -> unicode: ...
def translate(
    term: AnyStr, locale: Optional[AnyStr] = ..., strict: Optional[bool] = ...
) -> AnyStr: ...
