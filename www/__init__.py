"""
The module defines constants and an attribute dictionary class that facilitates
attribute-style access to dictionary keys. Additionally, it provides configuration
data for paths, templates, navigation, and various metadata for a structured web-based
application.

Classes:
- AttrDict: Extends the native Python dictionary to allow attribute-style access to
  dictionary keys.

Constants:
- ROOT: A string constant representing the root namespace or identifier.
- REPO: A string constant indicating the GitHub repository link.
- REPO_RELEASE: A string constant for the latest release API endpoint of the repository.
- REPO_COMMIT: A string constant for the master commit API endpoint of the repository.
- EXTENSION: The default file extension used in templates.
- STR_EMPTY: A constant representing an empty string.
- STR_SLASH: A constant for the slash character.
- STR_UNDER_CONSTR: A string constant indicating "under construction" status.
- STR_WIP: A string constant indicating "work in progress" status.

Structured dictionaries (instances of AttrDict):
- KEY: Contains attribute keys for path, ID, template, navigation, title, additional
  info, hints, and name.
- INDEX: Metadata for the index page, including path, template, navigation title, and
  other information.
- CAMS: Metadata for the live streams page with warnings about single access use.
- PRIVAT: Metadata for the privacy/legal notice page.
- POWER: Metadata for the power status page.
- SRVCS: Metadata for the services page, describing system services.
- MADE: Metadata for the "made in and for 3D" page, including its title, description,
  and status as a work in progress.
- STATUS: Metadata for a generic status page.

NAVI:
- A list of navigation elements, detailing the order, names, endpoints, IDs, and
  truncated titles for various sections in the application.
"""


class AttrDict(dict):
    """
    Attribute dictionary is the same as a python native dictionary, except
    that in most cases, you can use the dictionary key as if it was an
    object attribute instead. So it is possible to access items in the
    dictionary using attribute-style access and vice versa to set items in
    the dictionary. Keys must be of type string.
    """
    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


ROOT = "kobra"
REPO = "https://github.com/kaulketh/KobraPiV2"
REPO_RELEASE = ("https://api.github.com/repos/kaulketh/KobraPiV2/releases"
                "/latest")
REPO_COMMIT = "https://api.github.com/repos/kaulketh/KobraPiV2/commits/master"
EXTENSION = ".html"

STR_EMPTY = ""
STR_SLASH = "/"
STR_UNDER_CONSTR = "[ under construction ]"
STR_WIP = "[ work in progress ]"

KEY = AttrDict({"path": "path",
                "id": "id",
                "template": "template",
                "navi": "navi",
                "title": "title",
                "nfo": "info",
                "hint": "hint",
                "name": "name",
                "ep": "endpoint"
                })

INDEX = AttrDict({KEY.path: STR_SLASH,
                  KEY.id: "index",
                  KEY.template: f"index{EXTENSION}",
                  KEY.navi: "start",
                  KEY.title: "a dead cow, a kobra and four W",
                  KEY.nfo: STR_EMPTY,
                  KEY.hint: STR_EMPTY
                  })

CAMS = AttrDict({KEY.path: f"{STR_SLASH}cams",
                 KEY.id: "cams",
                 KEY.template: f"cams{EXTENSION}",
                 KEY.navi: "live",
                 KEY.title: "live streams",
                 KEY.nfo: "Turned off!",
                 KEY.hint: "Please make sure that these streams "
                           "have only been accessed ONCE!"
                 })

PRIVAT = AttrDict({KEY.path: f"{STR_SLASH}privacy",
                   KEY.id: "privacy",
                   KEY.template: f"privacy{EXTENSION}",
                   KEY.navi: STR_EMPTY,  # "imprint",
                   KEY.title: STR_EMPTY,  # "legal notice & privacy policy",
                   KEY.nfo: STR_EMPTY,
                   KEY.hint: STR_EMPTY
                   })

POWER = AttrDict({KEY.path: f"{STR_SLASH}power",
                  KEY.id: "power",
                  KEY.template: f"power{EXTENSION}",
                  KEY.navi: "power",
                  KEY.title: "power status",
                  KEY.nfo: STR_EMPTY,
                  KEY.hint: STR_EMPTY
                  })

SRVCS = AttrDict({KEY.path: f"{STR_SLASH}services",
                  KEY.template: f"services{EXTENSION}",
                  KEY.navi: "services",
                  KEY.id: "services",
                  KEY.title: "systemd services",
                  KEY.nfo: STR_EMPTY,
                  KEY.hint: STR_EMPTY
                  })

MADE = AttrDict({KEY.path: f"{STR_SLASH}made",
                 KEY.template: f"made{EXTENSION}",
                 KEY.navi: "made",
                 KEY.id: "made",
                 KEY.title: "what's possible",
                 KEY.nfo: "some impressions",
                 KEY.hint: STR_WIP
                 })

STATUS = AttrDict({KEY.path: f"{STR_SLASH}status"})

# navigation elements order
NAVI = [
    {KEY.name: INDEX.navi, KEY.ep: f"{ROOT}.{INDEX.id}",
     KEY.id: INDEX.id, KEY.title: f"{INDEX.title[:17]}..."},
    # {KEY.name: POWER.navi, KEY.ep: f"{ROOT}.{POWER.id}",
    # KEY.id: POWER.id, KEY.title: f"{POWER.title[:17]}..."},
    {KEY.name: CAMS.navi, KEY.ep: f"{ROOT}.{CAMS.id}",
     KEY.id: CAMS.id, KEY.title: f"{CAMS.title[:17]}..."},
    {KEY.name: SRVCS.navi, KEY.ep: f"{ROOT}.{SRVCS.id}",
     KEY.id: SRVCS.id, KEY.title: f"{SRVCS.title[:17]}..."},
    {KEY.name: MADE.navi, KEY.ep: f"{ROOT}.{MADE.id}",
     KEY.id: MADE.id, KEY.title: f"{MADE.title[:17]}..."}  # ,s
]
