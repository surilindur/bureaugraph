from typing import Dict
from typing import Sequence
from logging import INFO
from logging import DEBUG
from logging import ERROR
from logging import WARNING
from platform import python_version
from platform import system
from platform import machine
from platform import python_implementation
from platform import python_compiler
from platform import release

# The allowed levels for logging, to map from user input to integer values
AVAILABLE_LOG_LEVELS: Dict[str, int] = {
    "debug": DEBUG,
    "info": INFO,
    "warning": WARNING,
    "error": ERROR,
}

# The User-Agent header value that will be used in HTTP requests
USER_AGENT = " ".join(
    (
        f"Bureaugraph/1.0 ({system()} {machine()}; {python_compiler()})",
        f"{python_implementation()}/{python_version()}",
        f"{system()}/{release()}",
    )
)

# https://aclerkofoxford.blogspot.com/p/old-english-wisdom.html

# Patience is half of happiness (because the initial sync can take forever...)
STATUS_STARTUP = "Geþyld byþ middes eades."

STATUS_POOL: Sequence[str] = (
    # When you criticise another, remember no one is faultless.
    "Đonne ðu oþerne mon tæle, ðonne geðenc ðu þæt nan mon ne bið leahterleas.",
    # Don't argue with a stubborn person, or one who talks too much; many have the power of speech; very few of wisdom.
    "Ne flit ðu wið anwilne monn, ne wið oferspræcne; manegum menn is forgifen ðæt he spræcan mæg, swiðe feawum þæt he seo gesceadwis.",
    # Give more thanks for what you have than for what you're promised... Where little is promised, there's little deception.
    "Wite ðæs maran þanc ðæs ðe ðu hæbbe ðonne ðæs þe ðe monn gehate... ðær lytel gehaten bið, þær bið lytel alogen.",
    # Speak more often about other people’s good deeds than about your own.
    "Sprec ofter embe oðres monnes weldæde þonne emb ðine agna.",
    # Do not hope for another man's death; it is unknown who will live longest.
    "Ne hopa ðu to oþres monnes deaðe; uncuð hwa lengest libbe.",
    # Though a poor friend may give you little, take it with great thanks.
    "Đeah þe earm friond lytel sylle, nim hit to miccles þances.",
    # If you have children, teach them a skill, so they can live by it... A skill is better than possessions.
    "Gif ðu bearn hæbbe, lær þa cræftes, þæt hie mægen be þon libban... Cræft bið bætera þonne æht.",
    # Forbear often where you might easily take vengeance.
    "Forbær oft ðæt þu eaðe wrecan mæge.",
    # Help both friends and strangers wherever you can.
    "Help ægðer ge cuðum ge uncuþum þær þu mæge.",
    # Anger often disturbs a man's mind so that he cannot see the right.
    "Yrre oft amyrreð monnes mod þæt he ne mæg þæt riht gecnawan.",
    # Few men rejoice long in what they have got by deceiving others.
    "Lyt monna wearþ lange fægen ðæs ðe he oðerne bewrencþ.",
    # Don't do either of these things: praise yourself or criticise yourself.
    "Ne do ðu nauðer: ne ðe sylfne ne here, ne ðe sylfne ne leah.",
    # The more a man speaks, the less people believe him.
    "Swa mon ma spricð, swa him læs monna gelyfð.",
    # If you do something wrong when drunk, don’t blame it on the ale.
    "Gif ðu hwæt on druncen misdo, ne wit ðu hit ðam ealoþe."
    # Never become so sorrowful that you do not hope for better things.
    "Ne wurðe þe næfre to þys wa, þæt ðu þe ne wene betran.",
    # Every man's life may be a lesson to someone.
    "Ælces monnes lif bið sumes monnes lar.",
    # It’s foolish for a man to speak before he thinks.
    "Hit byð dysig þæt man speca ær þone he þænce.",
    # Scorn this world’s riches if you want to be rich in your mind.
    "Forseoh ðisse worlde wlenca gif ðu wille beon welig on ðinum modo.",
    # If you want to have a good reputation, don't rejoice in any evil.
    "Gif ðu wille godne hlisan habban, ne fægna ðu nanes yfeles.",
    # Always be learning something; though your good fortune may abandon you, don't abandon your skill.
    "Leorna a hwæthwugu; ðeah ðe þine gesælða forlætan, ne forlætt þe no þin cræft.",
    # Don't speak too much, but listen attentively to everyone's words.
    "Ne beo þu to oferspræce, ac hlyst ælces monnes worda swiðe georne.",
    # Learn something from the wise, so you can teach the ignorant.
    "Leorna hwæthwugu æt ðam wisran, þæt þu mæge læran þone unwisran.",
    # Do not leave unpraised anything you know well to be worthy.
    "Ne læt þu no unlofod þæt þu swytele ongite þæt licwyrðe sie.",
    # If an old friend angers you, don’t forget he once pleased you.
    "Đeah þe þin eald gefera abelge, ne forgit þu gif he þe... ær gecwemde",
    # Though many people praise you, do not believe them too readily.
    "Þeah ðe monig mon herige, ne gelyf ðu him to wel.",
    # Always be truer than people believe you to be.
    "Beo a getreowra ðonne ðe mon to gelyfe.",
    # He who is always afraid is like one who is always dying.
    "Se ðe him ealne weg ondræt, se bið swylce he sy ealne weg cwellende.",
    # In every river, the worse the ford the better the fish.
    "On ælcere ea swa wyrse fordes, swa betere fisces.",
)
