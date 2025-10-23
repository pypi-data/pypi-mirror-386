# ruff: noqa: TC003, TC001
from __future__ import annotations

from datetime import datetime

from pydantic import Field, RootModel, dataclasses

from betterKickAPI.object.base import KickObject
from betterKickAPI.object.eventsub import (
        AnonUserInfo,
        BannedMetadata,
        CompactUserInfo,
        Emote,
        KickGift,
        LivestreamMetadata,
        RepliedMessage,
        UserInfo,
)

__all__ = [
        "ChannelFollowEvent",
        "ChannelSubscriptionGiftsEvent",
        "ChannelSubscriptionNewEvent",
        "ChannelSubscriptionRenewalEvent",
        "ChatMessageEvent",
        "KicksGiftedEvent",
        "LivestreamMetadataUpdatedEvent",
        "LivestreamStatusUpdatedEvent",
        "RawEvent",
        "_CommonEventResponse",
]


@dataclasses.dataclass
class _CommonEventResponse(KickObject):
        pass


@dataclasses.dataclass
class ChatMessageEvent(_CommonEventResponse):
        message_id: str
        replies_to: RepliedMessage | None
        broadcaster: UserInfo
        sender: UserInfo
        content: str
        emotes: list[Emote] | None
        created_at: datetime


@dataclasses.dataclass
class ChannelFollowEvent(_CommonEventResponse):
        broadcaster: UserInfo
        follower: UserInfo


@dataclasses.dataclass
class _SubscriptionCommon(_CommonEventResponse):
        broadcaster: UserInfo
        subscriber: UserInfo
        duration: int
        created_at: datetime
        expires_at: datetime


class ChannelSubscriptionNewEvent(_SubscriptionCommon):
        pass


class ChannelSubscriptionRenewalEvent(_SubscriptionCommon):
        pass


@dataclasses.dataclass
class ChannelSubscriptionGiftsEvent(_CommonEventResponse):
        broadcaster: UserInfo
        created_at: datetime
        expires_at: datetime
        gifter: UserInfo | AnonUserInfo = Field(..., discriminator="is_anonymous")
        giftees: list[UserInfo] = Field(default_factory=list)


@dataclasses.dataclass
class LivestreamStatusUpdatedEvent(_CommonEventResponse):
        broadcaster: UserInfo
        is_live: bool
        title: str
        started_at: datetime
        ended_at: datetime | None


@dataclasses.dataclass
class LivestreamMetadataUpdatedEvent(_CommonEventResponse):
        broadcaster: UserInfo
        metadata: LivestreamMetadata


@dataclasses.dataclass
class ModerationBannedEvent(_CommonEventResponse):
        broadcaster: UserInfo
        moderator: UserInfo
        banned_user: UserInfo
        metadata: BannedMetadata


@dataclasses.dataclass
class KicksGiftedEvent(_CommonEventResponse):
        broadcaster: CompactUserInfo
        sender: CompactUserInfo
        gift: KickGift
        created_at: datetime


RawEvent = RootModel[dict]
