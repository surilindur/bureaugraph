from rdflib.term import URIRef
from rdflib.namespace import Namespace
from rdflib.namespace import DefinedNamespace

_DISCORD_URI = "https://discord.com"

# Utility namespace for Discord guilds
DISCORDGUILD = Namespace(f"{_DISCORD_URI}/guilds/")

# Utility namespace for Discord users
DISCORDUSER = Namespace(f"{_DISCORD_URI}/users/")

# Utility namespace for Discord roles
DISCORDROLE = Namespace(f"{_DISCORD_URI}/roles/")

# Utility namespace for Discord permissions
DISCORDPERMISSIONS = Namespace(f"{_DISCORD_URI}/permissions/")

# Utility namespace for Discord channels
DISCORDCHANNELS = Namespace(f"{_DISCORD_URI}/channels/")

# Utility namespace for Discord stickets
DISCORDSTICKERS = Namespace(f"{_DISCORD_URI}/stickers/")


class DISCORD(DefinedNamespace):
    """
    Custom imaginary ad-hoc Discord RDF namespace definition

    This is a quick mapping of some discord.py objects and their attributes
    into virtual RDF classes and objects, that are not actually defined in the
    namespace URI that is being used.

    https://discordpy.readthedocs.io/en/stable/api.html
    """

    _NS = Namespace(f"{_DISCORD_URI}/vocabulary/")

    Message: URIRef
    Role: URIRef
    User: URIRef
    Channel: URIRef
    Guild: URIRef
    Emoji: URIRef
    Attachment: URIRef
    GuildSticker: URIRef
    Snowflake: URIRef

    description: URIRef  # Textual description of a channel, attachment, etc.
    name: URIRef  # Name of guild, user, channel, attachment, emoji, etc.
    displayName: URIRef  # The name of a user that is displayed in a guild
    displayAvatar: URIRef  # The URI of a user's avatar in a guild
    bot: URIRef  # Boolean indicating whether the user is a bot
    system: URIRef  # Boolean indicating whether the user is a system user
    permission: URIRef  # The URI of a permission associated with a role
    sizeBytes: URIRef  # The size of something in bytes
    author: URIRef  # The URI of the author of a message
    content: URIRef  # The message content as a string
    channel: URIRef  # The URI of the channel of a message
    createdAt: URIRef  # Creation time of something as xsd:dateTime
    editedAt: URIRef  # Modification time of something as xsd:dateTime
    channelType: URIRef  # The type of a channel, represented as a string
    emoji: URIRef  # The unicode emoji that represents a sticker
    contentType: URIRef  # The mimetype of attachment or sticker
    widthPixels: URIRef  # Image width as xsd:integer
    heightPixels: URIRef  # Image height as xsd:integer
    attachment: URIRef  # The URI of an attachment associated with a message
    managed: URIRef  # Boolean indicating whether an emoji is managed externally
    animated: URIRef  # Boolean indicating whether an emoji is animated
    member: URIRef  # The URI of a member associated with a server
    nsfw: URIRef  # Boolean whether the channel is flagged as NSFW
    role: URIRef  # The URI of a role associated with a user
    icon: URIRef  # The URI of the server icon
    userLimit: URIRef  # The voice channel user limit as xsd:integer
    bitRate: URIRef  # The voice channel bitrate
    rtcRegion: URIRef  # The voice channel WebRTC region, represented as a string
    videoQualityMode: URIRef  # The voice channel video quality mode as a string
    permissionsSynced: URIRef  # Whether the permissions are synced with the category
    colour: URIRef  # Colour representation as hexadecimal
    category: URIRef  # The URI of the category of a guild channel
