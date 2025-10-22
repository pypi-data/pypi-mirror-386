# This is free and unencumbered software released into the public domain.

from .activity import Activity
from .airport import Airport
from .appointment import Appointment
from .audio_frame import AudioFrame
from .birth import Birth
from .birthday import Birthday
from .birthday_party import BirthdayParty
from .buddhist_temple import BuddhistTemple
from .cafe import Cafe
from .church import Church
from .class_ import Class
from .community import Community
from .company import Company
from .conference import Conference
from .congregation import Congregation
from .consortium import Consortium
from .corporation import Corporation
from .death import Death
from .event import Event
from .family import Family
from .file import File
from .government import Government
from .graduation import Graduation
from .group import Group
from .hindu_temple import HinduTemple
from .holiday import Holiday
from .hospital import Hospital
from .hotel import Hotel
from .image import Image
from .landmark import Landmark
from .link import Link
from .meeting import Meeting
from .meetup import Meetup
from .mosque import Mosque
from .nationality import Nationality
from .observation import Observation
from .organization import Organization
from .party import Party
from .percept import Percept, VisualPercept
from .person import Person
from .place import Place
from .pub import Pub
from .restaurant import Restaurant
from .school import School
from .synagogue import Synagogue
from .temple import Temple
from .thing import Thing
from .university import University
from .venue import Venue
from .wedding import Wedding


def loads(input: str | bytes | bytearray) -> Thing:
    import json
    import sys
    from typing import cast

    input_dict = json.loads(input)  # TODO: optimize this
    if "@type" in input_dict:
        input_type = str(input_dict["@type"])
        try:
            klass = cast(type[Thing], getattr(sys.modules[__name__], input_type))
            return klass.model_validate_json(input, by_alias=True)
        except AttributeError:
            pass
    return Thing(None, **input_dict)


def load(input: dict[str, object]) -> Thing:
    import sys
    from typing import cast

    if "@type" in input:
        input_type = str(input["@type"])
        try:
            klass = cast(type[Thing], getattr(sys.modules[__name__], input_type))
            return klass(None, **input)
        except AttributeError:
            pass
    return Thing(None, **input)
