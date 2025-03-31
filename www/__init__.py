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
WIP = "[ work in progress ]"
UNDER_CONSTR = "[ under construction ]"
SLASH = "/"

__EXT = ".html"
__EMPTY = ""
__K = AttrDict({"pth": "path",
                "id": "id",
                "tmpt": "template",
                "nav": "navi",
                "tit": "title",
                "nfo": "info",
                "hnt": "hint",
                "name": "name",
                "ep": "endpoint"
                })

INDEX = AttrDict({__K.pth: SLASH,
                  __K.id: "index",
                  __K.tmpt: f"index{__EXT}",
                  __K.nav: "start",
                  __K.tit: "a dead cow and a kobra",
                  __K.nfo: __EMPTY,
                  __K.hnt: __EMPTY
                  })

CAMS = AttrDict({__K.pth: f"{SLASH}cams",
                 __K.id: "cams",
                 __K.tmpt: f"cams{__EXT}",
                 __K.nav: "live",
                 __K.tit: "live streams",
                 __K.nfo: "Turned off!",
                 __K.hnt: "Please make sure that these streams "
                          "have only been accessed ONCE!"
                 })

POWER = AttrDict({__K.pth: f"{SLASH}power",
                  __K.id: "power",
                  __K.tmpt: f"power{__EXT}",
                  __K.nav: "power",
                  __K.tit: "power status",
                  __K.nfo: __EMPTY,
                  __K.hnt: __EMPTY
                  })

SRVCS = AttrDict({__K.pth: f"{SLASH}services",
                  __K.tmpt: f"services{__EXT}",
                  __K.nav: "services",
                  __K.id: "services",
                  __K.tit: "systemd services",
                  __K.nfo: __EMPTY,
                  __K.hnt: __EMPTY
                  })

ABOUT = AttrDict({__K.pth: f"{SLASH}about",
                  __K.tmpt: f"about{__EXT}",
                  __K.nav: "info",
                  __K.id: "about",
                  __K.tit: "information",
                  __K.nfo: __EMPTY,
                  __K.hnt: __EMPTY
                  })

MADE = AttrDict({__K.pth: f"{SLASH}made",
                 __K.tmpt: f"made{__EXT}",
                 __K.nav: "made",
                 __K.id: "made",
                 __K.tit: "made in and for 3D",
                 __K.nfo: WIP,
                 __K.hnt: __EMPTY
                 })

STATUS = AttrDict({__K.pth: f"{SLASH}status"})

# navigation elements order
NAVI = [
    {__K.name: INDEX.navi, __K.ep: f"{ROOT}.{INDEX.id}", __K.id: INDEX.id},
    {__K.name: POWER.navi, __K.ep: f"{ROOT}.{POWER.id}", __K.id: POWER.id},
    {__K.name: CAMS.navi, __K.ep: f"{ROOT}.{CAMS.id}", __K.id: CAMS.id},
    {__K.name: SRVCS.navi, __K.ep: f"{ROOT}.{SRVCS.id}", __K.id: SRVCS.id},
    {__K.name: ABOUT.navi, __K.ep: f"{ROOT}.{ABOUT.id}", __K.id: ABOUT.id},
    {__K.name: MADE.navi, __K.ep: f"{ROOT}.{MADE.id}", __K.id: MADE.id}
]
