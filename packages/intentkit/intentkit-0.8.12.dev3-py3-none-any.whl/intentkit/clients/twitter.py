import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, NotRequired, Optional, TypedDict
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from tweepy.asynchronous import AsyncClient

from intentkit.abstracts.twitter import TwitterABC
from intentkit.models.agent_data import AgentData
from intentkit.models.redis import get_redis

logger = logging.getLogger(__name__)

_clients_linked: Dict[str, "TwitterClient"] = {}
_clients_self_key: Dict[str, "TwitterClient"] = {}

_VERIFIER_KEY = "intentkit:twitter:code_verifier"
_CHALLENGE_KEY = "intentkit:twitter:code_challenge"


class TwitterMedia(BaseModel):
    """Model representing Twitter media from the API response."""

    media_key: str
    type: str
    url: Optional[str] = None


class TwitterUser(BaseModel):
    """Model representing a Twitter user from the API response."""

    id: str
    name: str
    username: str
    description: str
    public_metrics: dict = Field(
        description="User metrics including followers_count, following_count, tweet_count, listed_count, like_count, and media_count"
    )
    is_following: bool = Field(
        description="Whether the authenticated user is following this user",
        default=False,
    )
    is_follower: bool = Field(
        description="Whether this user is following the authenticated user",
        default=False,
    )


class Tweet(BaseModel):
    """Model representing a Twitter tweet."""

    id: str
    text: str
    author_id: str
    author: Optional[TwitterUser] = None
    created_at: datetime
    referenced_tweets: Optional[List["Tweet"]] = None
    attachments: Optional[List[TwitterMedia]] = None


class TwitterClientConfig(TypedDict):
    consumer_key: NotRequired[str]
    consumer_secret: NotRequired[str]
    access_token: NotRequired[str]
    access_token_secret: NotRequired[str]


class TwitterClient(TwitterABC):
    """Implementation of Twitter operations using Tweepy client.

    This class provides concrete implementations for interacting with Twitter's API
    through a Tweepy client, supporting both API key and OAuth2 authentication.

    Args:
        agent_id: The ID of the agent
        config: Configuration dictionary that may contain API keys
    """

    def __init__(self, agent_id: str, config: Dict) -> None:
        """Initialize the Twitter client.

        Args:
            agent_id: The ID of the agent
            config: Configuration dictionary that may contain API keys
        """
        self.agent_id = agent_id
        self._client: Optional[AsyncClient] = None
        self._agent_data: Optional[AgentData] = None
        self.use_key = _is_self_key(config)
        self._config = config

    async def _get_agent_data(self) -> AgentData:
        """Retrieve cached agent data, loading from the database if needed."""

        if not self._agent_data:
            self._agent_data = await AgentData.get(self.agent_id)
        return self._agent_data

    async def _refresh_agent_data(self) -> AgentData:
        """Reload agent data from the database."""

        self._agent_data = await AgentData.get(self.agent_id)
        return self._agent_data

    async def get_client(self) -> AsyncClient:
        """Get the initialized Twitter client.

        Returns:
            AsyncClient: The Twitter client if initialized
        """

        agent_data = await self._get_agent_data()

        if not self._client:
            # Check if we have API keys in config
            if self.use_key:
                self._client = AsyncClient(
                    consumer_key=self._config["consumer_key"],
                    consumer_secret=self._config["consumer_secret"],
                    access_token=self._config["access_token"],
                    access_token_secret=self._config["access_token_secret"],
                    return_type=dict,
                )
                # refresh userinfo if needed
                if not agent_data.twitter_self_key_refreshed_at or (
                    agent_data.twitter_self_key_refreshed_at
                    < datetime.now(tz=timezone.utc) - timedelta(days=1)
                ):
                    me = await self._client.get_me(
                        user_auth=self.use_key,
                        user_fields="id,username,name,verified",
                    )
                    if me and "data" in me and "id" in me["data"]:
                        await AgentData.patch(
                            self.agent_id,
                            {
                                "twitter_id": me["data"]["id"],
                                "twitter_username": me["data"]["username"],
                                "twitter_name": me["data"]["name"],
                                "twitter_is_verified": me["data"]["verified"],
                                "twitter_self_key_refreshed_at": datetime.now(
                                    tz=timezone.utc
                                ),
                            },
                        )
                    agent_data = await self._refresh_agent_data()
                logger.info(
                    f"Twitter self key client initialized. "
                    f"Use API key: {self.use_key}, "
                    f"User ID: {self.self_id}, "
                    f"Username: {self.self_username}, "
                    f"Name: {self.self_name}, "
                    f"Verified: {self.self_is_verified}"
                )
                return self._client
            # Otherwise try to get OAuth2 tokens from agent data
            if not agent_data.twitter_access_token:
                raise Exception(f"[{self.agent_id}] Twitter access token not found")
            if not agent_data.twitter_access_token_expires_at:
                raise Exception(
                    f"[{self.agent_id}] Twitter access token expiration not found"
                )
            if agent_data.twitter_access_token_expires_at <= datetime.now(
                tz=timezone.utc
            ):
                raise Exception(f"[{self.agent_id}] Twitter access token has expired")
            self._client = AsyncClient(
                bearer_token=agent_data.twitter_access_token,
                return_type=dict,
            )
            return self._client

        if not self.use_key:
            # check if access token has expired
            if agent_data.twitter_access_token_expires_at <= datetime.now(
                tz=timezone.utc
            ):
                agent_data = await self._refresh_agent_data()
                if agent_data.twitter_access_token_expires_at <= datetime.now(
                    tz=timezone.utc
                ):
                    raise Exception(
                        f"[{self.agent_id}] Twitter access token has expired"
                    )
                self._client = AsyncClient(
                    bearer_token=agent_data.twitter_access_token,
                    return_type=dict,
                )
                return self._client

        return self._client

    @property
    def self_id(self) -> Optional[str]:
        """Get the Twitter user ID.

        Returns:
            The Twitter user ID if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_id

    @property
    def self_username(self) -> Optional[str]:
        """Get the Twitter username.

        Returns:
            The Twitter username (without @ symbol) if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_username

    @property
    def self_name(self) -> Optional[str]:
        """Get the Twitter display name.

        Returns:
            The Twitter display name if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_name

    @property
    def self_is_verified(self) -> Optional[bool]:
        """Get the Twitter account verification status.

        Returns:
            The Twitter account verification status if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_is_verified

    def process_tweets_response(self, response: Dict[str, Any]) -> List[Tweet]:
        """Process Twitter API response and convert it to a list of Tweet objects.

        Args:
            response: Raw Twitter API response containing tweets data and includes.

        Returns:
            List[Tweet]: List of processed Tweet objects.
        """
        result = []
        if not response.get("data"):
            return result

        # Create lookup dictionaries from includes
        users_dict = {}
        if response.get("includes") and "users" in response.get("includes"):
            users_dict = {
                user["id"]: TwitterUser(
                    id=str(user["id"]),
                    name=user["name"],
                    username=user["username"],
                    description=user["description"],
                    public_metrics=user["public_metrics"],
                    is_following="following" in user.get("connection_status", []),
                    is_follower="followed_by" in user.get("connection_status", []),
                )
                for user in response.get("includes", {}).get("users", [])
            }

        media_dict = {}
        if response.get("includes") and "media" in response.get("includes"):
            media_dict = {
                media["media_key"]: TwitterMedia(
                    media_key=media["media_key"],
                    type=media["type"],
                    url=media.get("url"),
                )
                for media in response.get("includes", {}).get("media", [])
            }

        tweets_dict = {}
        if response.get("includes") and "tweets" in response.get("includes"):
            tweets_dict = {
                tweet["id"]: Tweet(
                    id=str(tweet["id"]),
                    text=tweet["text"],
                    author_id=str(tweet["author_id"]),
                    created_at=datetime.fromisoformat(
                        tweet["created_at"].replace("Z", "+00:00")
                    ),
                    author=users_dict.get(tweet["author_id"]),
                    referenced_tweets=None,  # Will be populated in second pass
                    attachments=None,  # Will be populated in second pass
                )
                for tweet in response.get("includes", {}).get("tweets", [])
            }

        # Process main tweets
        for tweet_data in response["data"]:
            tweet_id = tweet_data["id"]
            author_id = tweet_data["author_id"]

            # Process attachments if present
            attachments = None
            if (
                "attachments" in tweet_data
                and "media_keys" in tweet_data["attachments"]
            ):
                attachments = [
                    media_dict[media_key]
                    for media_key in tweet_data["attachments"]["media_keys"]
                    if media_key in media_dict
                ]

            # Process referenced tweets if present
            referenced_tweets = None
            if "referenced_tweets" in tweet_data:
                referenced_tweets = [
                    tweets_dict[ref["id"]]
                    for ref in tweet_data["referenced_tweets"]
                    if ref["id"] in tweets_dict
                ]

            # Create the Tweet object
            tweet = Tweet(
                id=str(tweet_id),
                text=tweet_data["text"],
                author_id=str(author_id),
                created_at=datetime.fromisoformat(
                    tweet_data["created_at"].replace("Z", "+00:00")
                ),
                author=users_dict.get(author_id),
                referenced_tweets=referenced_tweets,
                attachments=attachments,
            )
            result.append(tweet)

        return result

    async def upload_media(self, agent_id: str, image_url: str) -> List[str]:
        """Upload media to Twitter and return the media IDs.

        Args:
            agent_id: The ID of the agent.
            image_url: The URL of the image to upload.

        Returns:
            List[str]: A list of media IDs for the uploaded media.

        Raises:
            ValueError: If there's an error uploading the media.
        """
        # Get agent data to access the token
        agent_data = await AgentData.get(agent_id)
        if not agent_data.twitter_access_token:
            raise ValueError("Only linked X account can post media")

        media_ids = []
        # Download the image
        async with httpx.AsyncClient() as session:
            response = await session.get(image_url)
            if response.status_code == 200:
                # Create a temporary file to store the image
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name

                # tweepy is outdated, we need to use httpx call new API
                try:
                    # Upload the image directly to Twitter using the Media Upload API
                    headers = {
                        "Authorization": f"Bearer {agent_data.twitter_access_token}"
                    }

                    # Upload to Twitter's media/upload endpoint using multipart/form-data
                    upload_url = "https://api.twitter.com/2/media/upload"

                    # Get the content type from the response headers or default to image/jpeg
                    content_type = response.headers.get("content-type", "image/jpeg")

                    # Create a multipart form with the image file and required parameters
                    files = {
                        "media": (
                            "image",
                            open(tmp_file_path, "rb"),
                            content_type,
                        )
                    }

                    # Add required parameters according to new API
                    data = {"media_category": "tweet_image", "media_type": content_type}

                    upload_response = await session.post(
                        upload_url, headers=headers, files=files, data=data
                    )

                    if upload_response.status_code == 200:
                        media_data = upload_response.json()
                        if "data" in media_data and "id" in media_data["data"]:
                            media_ids.append(media_data["data"]["id"])
                        else:
                            raise ValueError(
                                f"Unexpected response format from Twitter media upload: {media_data}"
                            )
                    else:
                        raise ValueError(
                            f"Failed to upload image to Twitter. Status code: {upload_response.status_code}, Response: {upload_response.text}"
                        )
                finally:
                    # Clean up the temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
            else:
                raise ValueError(
                    f"Failed to download image from URL: {image_url}. Status code: {response.status_code}"
                )

        return media_ids


def _is_self_key(config: Dict) -> bool:
    return config.get("api_key_provider") == "agent_owner"


def get_twitter_client(agent_id: str, config: Dict) -> "TwitterClient":
    if _is_self_key(config):
        if agent_id not in _clients_self_key:
            _clients_self_key[agent_id] = TwitterClient(agent_id, config)
        return _clients_self_key[agent_id]
    if agent_id not in _clients_linked:
        _clients_linked[agent_id] = TwitterClient(agent_id, config)
    return _clients_linked[agent_id]


async def unlink_twitter(agent_id: str) -> AgentData:
    logger.info(f"Unlinking Twitter for agent {agent_id}")
    return await AgentData.patch(
        agent_id,
        {
            "twitter_id": None,
            "twitter_username": None,
            "twitter_name": None,
            "twitter_access_token": None,
            "twitter_access_token_expires_at": None,
            "twitter_refresh_token": None,
        },
    )


# this class is forked from:
# https://github.com/tweepy/tweepy/blob/main/tweepy/auth.py
# it is not maintained by the original author, bug need to be fixed
class OAuth2UserHandler(OAuth2Session):
    """OAuth 2.0 Authorization Code Flow with PKCE (User Context)
    authentication handler
    """

    def __init__(self, *, client_id, redirect_uri, scope, client_secret=None):
        super().__init__(client_id, redirect_uri=redirect_uri, scope=scope)
        if client_secret is not None:
            self.auth = HTTPBasicAuth(client_id, client_secret)
        else:
            self.auth = None
        self.code_verifier = None
        self.code_challenge = None

    async def get_authorization_url(self, agent_id: str, redirect_uri: str):
        """Get the authorization URL to redirect the user to

        Args:
            agent_id: ID of the agent to authenticate
            redirect_uri: URI to redirect to after authorization
        """
        if not self.code_challenge:
            try:
                kv = await get_redis()
                self.code_verifier = await kv.get(_VERIFIER_KEY)
                self.code_challenge = await kv.get(_CHALLENGE_KEY)
                if not self.code_verifier or not self.code_challenge:
                    self.code_verifier = self._client.create_code_verifier(128)
                    self.code_challenge = self._client.create_code_challenge(
                        self.code_verifier, "S256"
                    )
                    await kv.set(_VERIFIER_KEY, self.code_verifier)
                    await kv.set(_CHALLENGE_KEY, self.code_challenge)
            except Exception:
                self.code_verifier = self._client.create_code_verifier(128)
                self.code_challenge = self._client.create_code_challenge(
                    self.code_verifier, "S256"
                )
        state_params = {"agent_id": agent_id, "redirect_uri": redirect_uri}
        authorization_url, _ = self.authorization_url(
            "https://x.com/i/oauth2/authorize",
            state=urlencode(state_params),
            code_challenge=self.code_challenge,
            code_challenge_method="S256",
        )
        return authorization_url

    def get_token(self, authorization_response):
        """After user has authorized the app, fetch access token with
        authorization response URL
        """
        if not self.code_verifier or not self.code_challenge:
            raise ValueError("Code verifier or challenge not init")
        return super().fetch_token(
            "https://api.x.com/2/oauth2/token",
            authorization_response=authorization_response,
            auth=self.auth,
            include_client_id=True,
            code_verifier=self.code_verifier,
        )

    def refresh(self, refresh_token: str):
        """Refresh token"""
        return super().refresh_token(
            "https://api.x.com/2/oauth2/token",
            refresh_token=refresh_token,
            include_client_id=True,
        )
