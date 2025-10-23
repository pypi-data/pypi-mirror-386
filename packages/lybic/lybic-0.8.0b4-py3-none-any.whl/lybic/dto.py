# -*- coding: UTF-8 -*-
#
# Copyright (c) 2019-2025   Beijing Tingyu Technology Co., Ltd.
# Copyright (c) 2025        Lybic Development Team <team@lybic.ai, lybic@tingyutech.com>
# Copyright (c) 2025        Lu Yicheng <luyicheng@tingyutech.com>
#
# Author: AEnjoy <aenjoyable@163.com>
#
# These Terms of Service ("Terms") set forth the rules governing your access to and use of the website lybic.ai
# ("Website"), our web applications, and other services (collectively, the "Services") provided by Beijing Tingyu
# Technology Co., Ltd. ("Company," "we," "us," or "our"), a company registered in Haidian District, Beijing. Any
# breach of these Terms may result in the suspension or termination of your access to the Services.
# By accessing and using the Services and/or the Website, you represent that you are at least 18 years old,
# acknowledge that you have read and understood these Terms, and agree to be bound by them. By using or accessing
# the Services and/or the Website, you further represent and warrant that you have the legal capacity and authority
# to agree to these Terms, whether as an individual or on behalf of a company. If you do not agree to all of these
# Terms, do not access or use the Website or Services.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""dto.py provides all the data types used in the API."""
import uuid
from enum import Enum, unique
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, RootModel

from lybic._api import deprecated

# pylint: disable=invalid-name

# Strategy for handling extra fields in the lybic api response
# "ignore" means ignore extra fields, which will ensure that your SDK version remains compatible with the Lybic platform,
# but it may cause compatibility issues with future versions of the SDK.
# "forbid" means that the SDK will throw an error if it encounters extra fields in the response, which will force you to
# update your SDK when the Lybic platform is updated, and may have a certain impact on your online environment.
json_extra_fields_policy = "ignore"


class StatsResponseDto(BaseModel):
    """
    Organization Stats response.
    """
    mcpServers: int
    sandboxes: int
    projects: int


class McpServerPolicy(BaseModel):
    """
    MCP server sandbox policy.
    """
    sandboxShape: str = Field('', description="The shape of the sandbox created by the MCP server.")
    sandboxMaxLifetimeSeconds: int = Field(3600, description="The maximum lifetime of a sandbox.")
    sandboxMaxIdleTimeSeconds: int = Field(3600, description="The maximum idle time of a sandbox.")
    sandboxAutoCreation: bool = Field(False,
                                      description="Whether to create a new sandbox automatically when old sandbox is deleted. If not, new sandboxes will be created when calling computer use tools.")
    sandboxExposeRecreateTool: bool = Field(False, description="Whether to expose recreate tool to LLMs.")
    sandboxExposeRestartTool: bool = Field(False, description="Whether to expose restart tool to LLMs.")
    sandboxExposeDeleteTool: bool = Field(False, description="Whether to expose delete tool to LLMs.")


class McpServerResponseDto(BaseModel):
    """
    MCP server response.
    """
    id: str = Field(..., description="ID of the MCP server.")
    name: str = Field(..., description="Name of the MCP server.")
    createdAt: str = Field(..., description="Creation date of the MCP server.")
    defaultMcpServer: bool = Field(..., description="Whether this is the default MCP server for the organization.")
    projectId: str = Field(..., description="Project ID to which the MCP server belongs.")
    policy: McpServerPolicy
    currentSandboxId: Optional[str] = Field(None, description="ID of the currently connected sandbox.")


class ListMcpServerResponse(RootModel):
    """
    A list of MCP server responses.
    """
    root: List[McpServerResponseDto]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class CreateMcpServerDto(McpServerPolicy):
    """
    Create MCP server request.
    Only name is needed, other fields are optional.
    """
    name: str = Field(..., description="Name of the MCP server.")
    projectId: Optional[str] = Field('', description="Project to which the MCP server belongs to.")
    sandboxShape: str = Field('', description="The shape of the sandbox created by the MCP server.")

    sandboxMaxLifetimeSeconds: Optional[int] = Field(3600, description="The maximum lifetime of a sandbox.")
    sandboxMaxIdleTimeSeconds: Optional[int] = Field(3600, description="The maximum idle time of a sandbox.")
    sandboxAutoCreation: Optional[bool] = Field(False,
                                                description="Whether to create a new sandbox automatically when old sandbox is deleted. If not, new sandboxes will be created when calling computer use tools.")
    sandboxExposeRecreateTool: Optional[bool] = Field(False, description="Whether to expose recreate tool to LLMs.")
    sandboxExposeRestartTool: Optional[bool] = Field(False, description="Whether to expose restart tool to LLMs.")
    sandboxExposeDeleteTool: Optional[bool] = Field(False, description="Whether to expose delete tool to LLMs.")

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True

class Shape(BaseModel):
    """
    Represents a shape of a sandbox.
    """
    name: str = Field(..., description="Name of the shape.")
    description: str = Field(..., description="Description of the shape.")
    hardwareAcceleratedEncoding: bool = Field(False, description="Whether the shape supports hardware accelerated encoding.")
    pricePerHour: float = Field(..., description="This price acts as a multiplier, e.g. if it is set to 0.5, each hour of usage will be billed as 0.5 hours.")
    requiredPlanTier: float = Field(..., description="Required plan tier to use this shape.")
    os: Literal["Windows","Linux","Android"]
    virtualization: Literal["KVM","Container"]
    architecture: Literal["x86_64","aarch64"]

# Sandbox Schemas
class Sandbox(BaseModel):
    """
    Represents a sandbox environment.
    """
    id: str = Field(..., description="ID of the sandbox.")
    name: str = Field(..., description="Name of the sandbox.")
    expiredAt: str = Field(..., description="Deprecated, use `expiresAt` instead, will be removed in v1.0.0")
    expiresAt: str = Field(..., description="Expiration date of the sandbox.")
    createdAt: str = Field(..., description="Creation date of the sandbox.")
    projectId: str = Field(..., description="Project ID to which the sandbox belongs.")
    shapeName: Optional[str] = Field(None, description="Specs and datacenter of the sandbox.") # This field does not exist in GetSandboxResponseDto (that is, this field is optional)
    shape: Optional[Shape] = None # This field does not exist in SandboxListResponseDto (that is, this field is optional)
    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy


class GatewayAddress(BaseModel):
    """
    Details of a gateway address for connecting to a sandbox.
    """
    address: str
    port: int
    name: str
    preferredProviders: List[Literal["CHINA_MOBILE", "CHINA_UNICOM", "CHINA_TELECOM", "GLOBAL_BGP", 1, 2, 3, 4]]
    gatewayType: Literal["KCP", "QUIC", "WEB_TRANSPORT", "WEBSOCKET", 4, 5, 6, 7]


class ConnectDetails(BaseModel):
    """
    Connection details for a sandbox, including gateway addresses and authentication tokens.
    """
    gatewayAddresses: List[GatewayAddress]
    certificateHashBase64: str
    endUserToken: str
    roomId: str


class SandboxListItem(Sandbox):
    """
    An item in a list of sandboxes, containing sandbox details and connection information.
    """


class SandboxListResponseDto(RootModel):
    """
    A response DTO containing a list of sandboxes.
    """
    root: List[SandboxListItem]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class CreateSandboxDto(BaseModel):
    """
    Create sandbox request.
    """
    name: str = Field("sandbox", description="The name of the sandbox.")
    maxLifeSeconds: int = Field(3600,
                                description="The maximum life time of the sandbox in seconds. Default is 1 hour, max is 1 day.",
                                ge=1, le=86400)
    projectId: Optional[str] = Field(None, description="The project id to use for the sandbox. Use default if not provided.")
    shape: str = Field(..., description="Specs and datacenter of the sandbox.")

    class Config:
        """
        Configuration for Pydantic model.
        """
        exclude_none = True


class GetSandboxResponseDto(BaseModel):
    """
    A response DTO for a single sandbox, including connection details.
    """
    sandbox: Sandbox
    connectDetails: ConnectDetails


# Computer Use Schemas
class PixelLength(BaseModel):
    """
    Represents a length in pixels.
    """
    type: Literal["px"]
    value: int


class FractionalLength(BaseModel):
    """
    Represents a length as a fraction of a total dimension.
    """
    type: Literal["/"]
    numerator: int
    denominator: int


Length = Union[PixelLength, FractionalLength]


class MouseClickAction(BaseModel):
    """
    Represents a mouse click action at a specified location.
    """
    type: Literal["mouse:click"]
    x: Length
    y: Length
    button: int = Field(..., description="Mouse button flag combination. 1: left, 2: right, 4: middle, 8: back, 16: forward; add them together to press multiple buttons at once.")
    relative: bool = Field(False, description="Whether the coordinates are relative to the current mouse position")
    holdKey: Optional[str] = Field(None, description="Key to hold down during click, in xdotool key syntax. Example: \"ctrl\", \"alt\", \"alt+shift\"")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True

class MouseTripleClickAction(BaseModel):
    """
    Represents a mouse triple-click action at a specified location.
    """
    type: Literal["mouse:tripleClick"]
    x: Length
    y: Length
    button: int = Field(..., description="Mouse button flag combination. 1: left, 2: right, 4: middle, 8: back, 16: forward; add them together to press multiple buttons at once.")
    relative: bool = Field(False, description="Whether the coordinates are relative to the current mouse position.")
    holdKey: Optional[str] = Field(None, description="Key to hold down during triple click, in xdotool key syntax. Example: \"ctrl\", \"alt\", \"alt+shift\"")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True

class MouseDoubleClickAction(BaseModel):
    """
    Represents a mouse double-click action at a specified location.
    """
    type: Literal["mouse:doubleClick"]
    x: Length
    y: Length
    button: int = Field(..., description="Mouse button flag combination. 1: left, 2: right, 4: middle, 8: back, 16: forward; add them together to press multiple buttons at once.")
    relative: bool = Field(False, description="Whether the coordinates are relative to the current mouse position")
    holdKey: Optional[str] = Field(None, description="Key to hold down during click, in xdotool key syntax. Example: \"ctrl\", \"alt\", \"alt+shift\"")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class MouseMoveAction(BaseModel):
    """
    Represents a mouse move action to a specified location.
    """
    type: Literal["mouse:move"]
    x: Length
    y: Length
    relative: bool = Field(False, description="Whether the coordinates are relative to the current mouse position")
    holdKey: Optional[str] = Field(None, description="Key to hold down during move, in xdotool key syntax. Example: \"ctrl\", \"alt\", \"alt+shift\"")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class MouseScrollAction(BaseModel):
    """
    Represents a mouse scroll action.
    """
    type: Literal["mouse:scroll"]
    x: Length
    y: Length
    stepVertical: int
    stepHorizontal: int
    relative: bool = Field(False, description="Whether the coordinates are relative to the current mouse position")
    holdKey: Optional[str] = Field(None, description="Key to hold down during scroll, in xdotool key syntax. Example: \"ctrl\", \"alt\", \"alt+shift\"")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class MouseDragAction(BaseModel):
    """
    Represents a mouse drag action from a start to an end point.
    """
    type: Literal["mouse:drag"]
    startX: Length
    startY: Length
    endX: Length
    endY: Length
    startRelative: bool = Field(False, description="Whether the start coordinates are relative to the current mouse position.")
    endRelative: bool = Field(False, description="Whether the end coordinates are relative to the start coordinates of the drag. If false, they are absolute screen coordinates.")
    button: int = Field(..., description="Mouse button flag combination. 1: left, 2: right, 4: middle, 8: back, 16: forward; add them together to press multiple buttons at once.")
    holdKey: Optional[str] = Field(None, description="Key to hold down during drag, in xdotool key syntax. Example: \"ctrl\", \"alt\", \"alt+shift\"")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class KeyboardTypeAction(BaseModel):
    """
    Represents a keyboard typing action.
    """
    type: Literal["keyboard:type"]
    content: str
    treatNewLineAsEnter: bool = Field(False, description="Whether to treat line breaks as enter. If true, any line breaks(\\n) in content will be treated as enter key press, and content will be split into multiple lines.")
    callId: Optional[str] = str(uuid.uuid4())


class KeyboardHotkeyAction(BaseModel):
    """
    Represents a keyboard hotkey combination action.
    """
    type: Literal["keyboard:hotkey"]
    keys: str
    duration: Optional[int] = Field(None, description="Duration in milliseconds. If specified, the hotkey will be held for a while and then released.")
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class ScreenshotAction(BaseModel):
    """
    Represents an action to take a screenshot.
    """
    type: Literal["screenshot"]
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class WaitAction(BaseModel):
    """
    Represents a wait action for a specified duration.
    """
    type: Literal["wait"]
    duration: int
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class FinishedAction(BaseModel):
    """
    Represents a finished action, signaling successful completion of a task.
    """
    type: Literal["finished"]
    message: Optional[str] = None
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class FailedAction(BaseModel):
    """
    Represents a failed action, signaling an error or failure in a task.
    """
    type: Literal["failed"]
    message: Optional[str] = None
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


ComputerUseAction = Union[
    MouseClickAction,
    MouseTripleClickAction,
    MouseDoubleClickAction,
    MouseMoveAction,
    MouseScrollAction,
    MouseDragAction,
    KeyboardTypeAction,
    KeyboardHotkeyAction,
    ScreenshotAction,
    WaitAction,
    FinishedAction,
    FailedAction,
]


@deprecated(
    since="0.8.0",
    removal="1.0.0",
    message="Use `ExecuteSandboxActionDto` instead, which supports both computer and mobile use actions."
)
class ComputerUseActionDto(BaseModel):
    """
    Computer use action request.
    """
    action: ComputerUseAction | dict
    includeScreenShot: bool = True
    includeCursorPosition: bool = True
    callId: Optional[str] = str(uuid.uuid4())

    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True


class CursorPosition(BaseModel):
    """
    Represents the position of the cursor on the screen.
    """
    x: int
    y: int
    screenWidth: int
    screenHeight: int
    screenIndex: int


class ExtendSandboxDto(BaseModel):
    """
    Extend sandbox life request.
    """
    maxLifeSeconds: int = Field(3600, description="Max life seconds of sandbox", ge=30, le=60 * 60 * 24)


class SandboxActionResponseDto(BaseModel):
    """
    Computer use action response.
    """
    screenShot: Optional[str]  # is a picture url of the screen eg. https://example.com/screen.webp
    cursorPosition: Optional[CursorPosition]


@unique
class ModelType(Enum):
    """
    Enumeration of supported LLM models for computer-use parsing.
    """
    UITARS = "ui-tars"
    SEED = "seed"
    GLM_4_1V = "glm-4.1v"
    GLM_4_5V = "glm-4.5v"
    QWEN_2_5_VL = "qwen-2.5-vl"
    PYAUTOGUI = "pyautogui"


class ParseTextRequestDto(BaseModel):
    """
    Request DTO for parsing text content.
    """
    textContent: str


@deprecated(
    since="0.7.0",
    removal="1.0.0",
    message=(
        "Starting from v0.7.0, parsing LLM output functions(ComputerUse.parse_llm_output) will "
        "no longer require ComputerUseParseRequestDto"
    )
)
class ComputerUseParseRequestDto(BaseModel):
    """
    Request DTO for parsing text content into computer use actions.
    """
    model: Literal["ui-tars", "oai-compute-use", "seed"]
    textContent: str


class ComputerUseActionResponseDto(BaseModel):
    """
    Response DTO containing a list of parsed computer use actions.
    """
    unknown: Optional[str] = None
    thoughts: Optional[str] = None
    memory: Optional[str] = None

    actions: List[ComputerUseAction]


# Mobile Use Schemas
class MobileTapAction(BaseModel):
    """
    Represents a mobile tap action.
    """
    type: Literal["mobile:tap"]
    x: Length
    y: Length
    callId: Optional[str] = str(uuid.uuid4())


class MobileDoubleTapAction(BaseModel):
    """
    Represents a mobile double tap action.
    """
    type: Literal["mobile:doubleTap"]
    x: Length
    y: Length
    callId: Optional[str] = str(uuid.uuid4())


class MobileSwipeAction(BaseModel):
    """
    Represents a mobile swipe action.
    """
    type: Literal["mobile:swipe"]
    startX: Length
    startY: Length
    endX: Length
    endY: Length
    duration: int
    callId: Optional[str] = str(uuid.uuid4())


class MobileTypeAction(BaseModel):
    """
    Represents a mobile type action.
    """
    type: Literal["mobile:type"]
    content: str
    callId: Optional[str] = str(uuid.uuid4())


class MobileHotkeyAction(BaseModel):
    """
    Represents a mobile hotkey action.
    """
    type: Literal["mobile:hotkey"]
    key: str
    callId: Optional[str] = str(uuid.uuid4())


class MobileHomeAction(BaseModel):
    """
    Represents a mobile home action.
    """
    type: Literal["mobile:home"]
    callId: Optional[str] = str(uuid.uuid4())


class MobileBackAction(BaseModel):
    """
    Represents a mobile back action.
    """
    type: Literal["mobile:back"]
    callId: Optional[str] = str(uuid.uuid4())


class MobileScreenshotAction(BaseModel):
    """
    Represents a mobile screenshot action.
    """
    type: Literal["mobile:screenshot"]
    callId: Optional[str] = str(uuid.uuid4())


class MobileWaitAction(BaseModel):
    """
    Represents a mobile wait action.
    """
    type: Literal["mobile:wait"]
    duration: int
    callId: Optional[str] = str(uuid.uuid4())


class MobileFinishedAction(BaseModel):
    """
    Represents a mobile finished action.
    """
    type: Literal["mobile:finished"]
    message: Optional[str] = None
    callId: Optional[str] = str(uuid.uuid4())


class MobileFailedAction(BaseModel):
    """
    Represents a mobile failed action.
    """
    type: Literal["mobile:failed"]
    message: Optional[str] = None
    callId: Optional[str] = str(uuid.uuid4())


MobileUseAction = Union[
    MobileTapAction,
    MobileDoubleTapAction,
    MobileSwipeAction,
    MobileTypeAction,
    MobileHotkeyAction,
    MobileHomeAction,
    MobileBackAction,
    MobileScreenshotAction,
    MobileWaitAction,
    MobileFinishedAction,
    MobileFailedAction,
]


Action = Union[ComputerUseAction, MobileUseAction]


class ExecuteSandboxActionDto(BaseModel):
    """
    Sandbox action request, supporting both computer and mobile use actions.
    """
    action: Action | dict
    includeScreenShot: bool = True
    includeCursorPosition: bool = True
    callId: Optional[str] = str(uuid.uuid4())


# Project Schemas
class ProjectResponseDto(BaseModel):
    """
    Get Project Response
    """
    id: str
    name: str
    createdAt: str
    defaultProject: bool


class ListProjectsResponseDto(RootModel):
    """
    A response DTO containing a list of projects.
    """
    root: List[ProjectResponseDto]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class CreateProjectDto(BaseModel):
    """
    Data transfer object for creating a new project.
    """
    name: str


class SingleProjectResponseDto(ProjectResponseDto):
    """
    Response DTO for a single project.
    """


class SetMcpServerToSandboxResponseDto(BaseModel):
    """
    Response DTO for setting a MCP server to a sandbox.
    """
    sandboxId: Optional[str] = Field(None, description="The ID of the sandbox to connect the MCP server to.")


class Shapes(BaseModel):
    """
    Shapes
    """
    name: str
    description: str
    hardwareAcceleratedEncoding: bool
    pricePerHour: str
    requiredPlanTier: int
    os: str
    virtualization:  str
    architecture:  str
    class Config:
        """
        Configuration for Pydantic model.
        """
        extra = json_extra_fields_policy
        # Allow population of fields with default values
        validate_assignment = True
        exclude_none = True

class GetShapesResponseDto(RootModel):
    """
    Response DTO for getting shapers.
    """
    root: List[Shapes]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
