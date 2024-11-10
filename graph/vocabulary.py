from rdflib.term import URIRef
from rdflib.namespace import Namespace
from rdflib.namespace import DefinedNamespace

DISCORD_URI = "https://discord.com"


class DISCORD(DefinedNamespace):
    """
    Custom imaginary ad-hoc Discord RDF namespace definition

    This is a quick mapping of some discord.py objects and their attributes
    into virtual RDF classes and objects, that are not actually defined in the
    namespace URI that is being used.
    """

    _NS = Namespace(f"{DISCORD_URI}/vocabulary/")

    Attachment: URIRef
    Channel: URIRef
    Emoji: URIRef
    Guild: URIRef
    GuildSticker: URIRef
    Message: URIRef
    Role: URIRef
    ScheduledEvent: URIRef
    Snowflake: URIRef
    StageInstance: URIRef
    Thread: URIRef
    User: URIRef

    animated: URIRef  # Boolean indicating whether an emoji is animated
    archived: URIRef  # Boolean indicating whether a thread had been archived
    archivedAt: URIRef  # Datetime indicating when a thread has been archived
    attachment: URIRef  # The URI of an attachment associated with a message
    author: URIRef  # The URI of the author of a message
    avatar: URIRef  # The URI of the avatar of a user
    bitRate: URIRef  # The voice channel bitrate
    bot: URIRef  # Boolean indicating whether the user is a bot
    category: URIRef  # The URI of the category of a guild channel
    channel: URIRef  # The URI of the channel of a message
    channelType: URIRef  # The type of a channel, represented as a string
    colour: URIRef  # Colour representation as hexadecimal
    content: URIRef  # The message content as a string
    contentType: URIRef  # The mimetype of attachment or sticker
    createdAt: URIRef  # Creation time of something as xsd:dateTime
    description: URIRef  # Textual description of a channel, attachment, etc.
    discoverableDisabled: URIRef  # Something related to StageInstances
    displayName: URIRef  # The name of a user that is displayed in a guild
    displayAvatar: URIRef  # The URI of a user's avatar in a guild
    editedAt: URIRef  # Modification time of something as xsd:dateTime
    emoji: URIRef  # The unicode emoji that represents a sticker
    endTime: URIRef  # The end time of a scheduled event
    globalName: URIRef  # The global name of a user
    heightPixels: URIRef  # Image height as xsd:integer
    icon: URIRef  # The URI of the server icon
    locationType: URIRef  # The location type of a scheduled event
    managed: URIRef  # Boolean indicating whether an emoji is managed externally
    member: URIRef  # The URI of a member associated with a server
    name: URIRef  # Name of guild, user, channel, attachment, emoji, etc.
    nsfw: URIRef  # Boolean whether the channel is flagged as NSFW
    parent: URIRef  # The parent channel of a Thread
    permission: URIRef  # The URI of a permission associated with a role
    permissionsSynced: URIRef  # Whether the permissions are synced with the category
    privacyLevel: URIRef  # The privacy level of a StageInstance
    role: URIRef  # The URI of a role associated with a user
    rtcRegion: URIRef  # The voice channel WebRTC region, represented as a string
    sizeBytes: URIRef  # The size of something in bytes
    startTime: URIRef  # The start time of a scheduled event
    status: URIRef  # The status of a scheduled event
    system: URIRef  # Boolean indicating whether the user is a system user
    userLimit: URIRef  # The voice channel user limit as xsd:integer
    videoQualityMode: URIRef  # The voice channel video quality mode as a string
    widthPixels: URIRef  # Image width as xsd:integer
