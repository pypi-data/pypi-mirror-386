from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from layrz_sdk.entities.asset import Asset
from layrz_sdk.entities.destination_phone import DestinationPhone
from layrz_sdk.entities.geofence import Geofence
from layrz_sdk.entities.locator import Locator
from layrz_sdk.entities.notification_type import TwilioNotificationType
from layrz_sdk.entities.operation import Operation
from layrz_sdk.entities.operation_case_payload import OperationCasePayload
from layrz_sdk.entities.operation_type import OperationType
from layrz_sdk.entities.platform import Platform
from layrz_sdk.entities.presence_type import PresenceType
from layrz_sdk.entities.request_type import HttpRequestType
from layrz_sdk.entities.sound_effect import SoundEffect
from layrz_sdk.entities.trigger import Trigger


class OperationPayload(BaseModel):
  """Operation Payload entity"""

  model_config = ConfigDict(
    validate_by_name=False,
    validate_by_alias=True,
    serialize_by_alias=True,
  )

  kind: OperationType = Field(
    ...,
    description='Defines the kind of the operation',
    alias='operationType',
  )

  @field_serializer('kind', when_used='always')
  def serialize_kind(self, value: OperationType) -> str:
    return value.value

  asset: Asset = Field(..., description='Defines the asset associated with the operation')

  @field_validator('asset', mode='before')
  def validate_asset(cls, value: Any) -> Asset:
    """Serialize asset to a dictionary"""
    if isinstance(value, Asset):
      return Asset(
        id=value.pk,  # ty: ignore
        name=value.name,
        operation_mode=value.operation_mode,
        vin=value.vin,
        plate=value.plate,
        custom_fields=value.custom_fields,
        contacts=value.contacts,
      )

    if isinstance(value, dict):
      return Asset.model_validate(value)

    raise ValueError('Asset must be an instance of Asset or a dictionary')

  trigger: Trigger = Field(..., description='Defines the trigger associated with the operation')

  @field_validator('trigger', mode='before')
  def validate_trigger(cls, value: Any) -> Trigger:
    """Serialize trigger to a dictionary"""
    if isinstance(value, Trigger):
      return Trigger(
        id=value.pk,  # ty: ignore
        name=value.name,
        code=value.code,
      )

    if isinstance(value, dict):
      return Trigger.model_validate(value)

    raise ValueError('Trigger must be an instance of Trigger or a dictionary')

  operation: Operation = Field(..., description='Defines the operation associated with the payload')

  @field_validator('operation', mode='before')
  def validate_operation(cls, value: Any) -> Operation:
    """Serialize operation to a dictionary"""
    if isinstance(value, Operation):
      return Operation(
        id=value.pk,  # ty: ignore
        name=value.name,
        operation_type=value.kind,
        timezone=value.timezone,
      )

    if isinstance(value, dict):
      return Operation.model_validate(value)

    raise ValueError('Operation must be an instance of Operation or a dictionary')

  activated_at: datetime = Field(
    ...,
    description='Defines the date when the operation was activated',
    alias='activatedAt',
  )

  @field_serializer('activated_at', when_used='always')
  def serialize_activated_at(self, value: datetime) -> float:
    return value.timestamp()

  position: dict[str, Any] = Field(
    default_factory=dict,
    description='Defines the position of the operation',
  )

  sensors: dict[str, Any] = Field(
    default_factory=dict,
    description='Defines the sensors of the operation',
  )

  geofence: Geofence | None = Field(
    default=None,
    description='Defines the geofence of the operation',
  )

  presence_type: PresenceType | None = Field(
    default=None,
    description='Defines the presence type of the operation',
    alias='presenceType',
  )

  @field_serializer('presence_type', when_used='always')
  def serialize_presence_type(self, value: PresenceType | None) -> Any:
    return value.value if value else None

  case_: OperationCasePayload | None = Field(
    default=None,
    description='Defines the case of the operation',
    alias='case',
  )

  language_id: int = Field(
    default=2,
    description='Defines the language ID of the operation',
    alias='languageId',
  )

  payload: str = Field(
    default='',
    description='Defines the payload of the operation',
  )

  use_asset_contacts_instead: bool = Field(
    default=False,
    description='Defines if the operation should use asset contacts instead of reception emails',
    alias='useAssetContactsInstead',
  )

  account_id: int | str | None = Field(
    default=None,
    description='Defines the external account ID of the operation',
    alias='accountId',
  )

  ## For usage of Webhooks operations
  http_url: str | None = Field(
    default=None,
    description='Defines the URL of the operation',
  )
  http_method: HttpRequestType | None = Field(
    default=None,
    description='Defines the HTTP method of the operation',
    alias='method',
  )

  @field_serializer('http_method', when_used='always')
  def serialize_http_method(self, value: HttpRequestType | None) -> Any:
    return value.value if value else None

  http_headers: list[dict[str, Any]] = Field(
    default_factory=list,
    description='Defines the headers of the operation',
    alias='headers',
  )

  ## For usage of Email operations
  email_subject: str = Field(
    default='',
    description='Defines the email subject of the operation',
    alias='emailSubject',
  )

  attach_image: bool = Field(
    default=False,
    description='Defines if the operation should attach an image',
    alias='attachImage',
  )

  reception_emails: list[str] = Field(
    default_factory=list,
    description='Defines the reception emails of the operation',
    alias='receptionEmails',
  )

  template_id: int | None = Field(
    default=None,
    description='Defines the template ID of the operation',
    alias='templateId',
  )

  ## For usage of Twilio operations
  destinations: list[DestinationPhone] = Field(
    default_factory=list,
    description='Defines the destination phone numbers for Twilio notifications',
  )

  @field_validator('destinations', mode='before')
  def serialize_destinations(cls, value: Any) -> list[DestinationPhone]:
    """Serialize destinations to a list of DestinationPhone"""
    if isinstance(value, list):
      return value

    if isinstance(value, DestinationPhone):
      return [value]

    return []

  twilio_host_phone: DestinationPhone | None = Field(
    default=None,
    description='Defines the host phone number for Twilio notifications',
    alias='hostPhone',
  )

  @field_validator('twilio_host_phone', mode='before')
  def serialize_twilio_host_phone(cls, value: Any) -> DestinationPhone | None:
    """Serialize host phone to a DestinationPhone"""
    if isinstance(value, DestinationPhone):
      return value

    if isinstance(value, dict):
      return DestinationPhone.model_validate(value)

    return None

  twilio_notification_type: TwilioNotificationType = Field(
    default=TwilioNotificationType.SMS,
    description='Defines the Twilio notification type of the operation',
    alias='notificationType',
  )

  @field_serializer('twilio_notification_type', when_used='always')
  def serialize_twilio_notification_type(self, value: TwilioNotificationType) -> str:
    return value.value

  username: str | None = Field(
    default=None,
    description='Defines the username for the operation',
  )

  token: str | None = Field(
    default=None,
    description='Defines the token for the operation',
  )

  requires_bhs_validation: bool = Field(
    default=False,
    description='Defines if the operation requires BHS validation',
    alias='requiresBhsValidation',
  )

  bhs_tier_id: int | None = Field(
    default=None,
    description='Defines the BHS tier ID for the operation',
    alias='bhsTierId',
  )

  ## For usage of BHS Push operations
  push_title: str = Field(
    default='',
    description='Defines the title for push notifications',
    alias='pushTitle',
  )

  push_platforms: list[Platform] = Field(
    default_factory=list,
    description='Defines the platforms for push notifications',
    alias='pushPlatforms',
  )

  @field_serializer('push_platforms', when_used='always')
  def serialize_push_platforms(self, value: list[Platform]) -> list[str]:
    return [platform.value for platform in value]

  ## For usage of In-app notifications operations
  destinations_ids: list[int] = Field(
    default_factory=list,
    description='Defines the destination IDs for in-app notifications',
    alias='destinationsIds',
  )
  sound_effect: SoundEffect = Field(
    default=SoundEffect.NONE,
    description='Defines the sound effect for the operation',
    alias='soundEffect',
  )

  @field_serializer('sound_effect', when_used='always')
  def serialize_sound_effect(self, value: SoundEffect) -> str:
    return value.value

  sound_effect_uri: str | None = Field(
    default=None,
    description='Defines the sound effect URI for the operation',
    alias='soundEffectUri',
  )

  icon: str | None = Field(
    default=None,
    description='Defines the icon for the in-app notification',
    alias='icon',
  )

  duration: timedelta | None = Field(
    default_factory=lambda: timedelta(seconds=0),
    description='Defines the duration of the in-app notification',
    alias='duration',
  )

  @field_validator('duration', mode='before')
  def validate_duration(cls, value: Any) -> timedelta:
    if value is None:
      return timedelta(seconds=0)
    if isinstance(value, timedelta):
      return value
    if isinstance(value, (int, float)):
      return timedelta(seconds=value)
    return timedelta(seconds=0)

  @field_serializer('duration', when_used='always')
  def serialize_duration(self, value: timedelta) -> float:
    return value.total_seconds()

  locator: Locator | None = Field(
    default=None,
    description='Defines the generated locator for the operation',
  )
