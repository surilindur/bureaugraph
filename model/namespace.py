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


class DISCORD(DefinedNamespace):
    """
    Custom imaginary ad-hoc Discord RDF namespace definition

    This is a quick mapping of some discord.py objects and their attributes
    into virtual RDF classes and objects, that are not actually defined in the
    namespace URI that is being used.
    """

    _NS = Namespace(f"{_DISCORD_URI}/vocabulary/")

    Message: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#message
    Role: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#role
    User: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#user
    Channel: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#guildchannel
    Guild: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#guild
    Emoji: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#discord.Emoji
    Attachment: URIRef  # https://discordpy.readthedocs.io/en/stable/api.html#attachment
    Snowflake: URIRef

    description: URIRef  # Description of an attachment or a text channel
    name: URIRef  # Name of a user, channel, attachment, role, etc.
    displayName: URIRef  # The display name of a user, that is shown in the member lists
    displayAvatar: URIRef  # User avatar URI
    bot: URIRef  # Whether the user is a bot
    system: URIRef  # Whether the user is a system user
    permission: URIRef  # Permission name as xsd:string
    sizeBytes: URIRef  # Size of something in bytes
    author: URIRef  # The author of a message
    content: URIRef  # Message content
    channel: URIRef  # Link from server to a channel
    createdAt: URIRef  # Creation time as xsd:dateTime
    editedAt: URIRef  # Modification time as xsd:dateTime
    contentType: URIRef  # Content mimetype
    widthPixels: URIRef  # Width as xsd:integer
    heightPixels: URIRef  # Height as xsd:integer
    attachment: URIRef  # Link from message to attachment
    managed: URIRef  # Whether the emoji is managed externally
    animated: URIRef  # Whether the emoji is animated
    member: URIRef  # Link from server to a user
    nsfw: URIRef  # Channel NSFW flag as xsd:boolean
    role: URIRef  # Link from user to a role
    icon: URIRef  # Server icon URI
    userLimit: URIRef  # Voice channel user limit as xsd:integer
    bitRate: URIRef  # Voice channel bitrate
    rtcRegion: URIRef  # Voice channel WebRTC region
    videoQualityMode: URIRef  # Voice channel video quality mode
    permissionsSynced: URIRef  # Whether the permissions are synced with the category
    colour: URIRef  # Colour representation as hex xsd:string
    category: URIRef  # The category of a guild channel
