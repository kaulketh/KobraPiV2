class AttrDict(dict):
    """
    Attribute Dictionary, is the same as a python native dictionary,except
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
                  KEY.title: "a dead cow and a kobra or three W and a M",
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
                 KEY.title: "made in and for 3D",
                 KEY.nfo: "some impressions",
                 KEY.hint: STR_WIP
                 })

STATUS = AttrDict({KEY.path: f"{STR_SLASH}status"})

# navigation elements order
NAVI = [
    {KEY.name: INDEX.navi, KEY.ep: f"{ROOT}.{INDEX.id}",
     KEY.id: INDEX.id, KEY.title: f"{INDEX.title[:17]}..."},
    {KEY.name: POWER.navi, KEY.ep: f"{ROOT}.{POWER.id}",
     KEY.id: POWER.id, KEY.title: f"{POWER.title[:17]}..."},
    {KEY.name: CAMS.navi, KEY.ep: f"{ROOT}.{CAMS.id}",
     KEY.id: CAMS.id, KEY.title: f"{CAMS.title[:17]}..."},
    {KEY.name: SRVCS.navi, KEY.ep: f"{ROOT}.{SRVCS.id}",
     KEY.id: SRVCS.id, KEY.title: f"{SRVCS.title[:17]}..."},
    {KEY.name: MADE.navi, KEY.ep: f"{ROOT}.{MADE.id}",
     KEY.id: MADE.id, KEY.title: f"{MADE.title[:17]}..."}  # ,s
]
