import logging
import random
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, List, Optional, Set, TypeVar, Generic, Union
from uuid import UUID
import json
from multipledispatch import dispatch
from functools import reduce
from pyrsistent import PClass, field
from pyrsistent import v, pvector, PVector
import numpy as np
from functools import cmp_to_key
from itertools import combinations as itertools_combinations, chain
from collections import deque
import copy
import hashlib
import os

DEFAULT_ALLOTTED_SECONDS = 60
INITIAL_ALLOTTED_SECONDS = 120
NUM_RANDOM_WALKS = 100 # 500

class NoAction(PClass):
    pass

class RouteDiscardAction(PClass):
    pass

class DrawUnitDeckAction(PClass):
    pass

class DrawUnitFaceupAction(PClass):
    pass

class ClaimPointAction(PClass):
    pass

class MovePiecesToPathAction(PClass):
    pass


class TrueType(PClass):
    pass

class FalseType(PClass):
    pass


def generate_uuid_with_rng(rng):
    # uuid4 uses 128 bits, but we need 16 bytes (128 bits) for the UUID
    # Generate 16 random bytes using the seeded rng
    random_bytes = bytes(rng.getrandbits(8) for _ in range(16))
    # Create a UUID from the random bytes
    return UUID(bytes=random_bytes, version=4)


def getbooltype(bool):
    if bool:
        return TrueType()
    return FalseType()


class FrozenLenScore(PClass):
    length = field(type=int)
    score = field(type=int)
    def __todict__(self):
        return {
            "len": self.length,
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenLenScore(
            length=d["len"],
            score=d["score"]
        )


class Hook(PClass):
    uuid = field(type=str)
    name = field(type=str)
    when = field(type=str)
    code = field(type=str)
    def __todict__(self):
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "when": self.when,
            "code": self.code,
        }
    @staticmethod
    def __fromdict__(d):
        return Hook(
            uuid=str(d["uuid"]),
            name=d["name"],
            when=d["when"],
            code=d["code"],
        )


class FrozenLink2(PClass):
    num = field(type=int)
    uuid = field(type=str)
    c1 = field(type=str)
    c2 = field(type=str)
    length = field(type=int)
    width = field(type=int)
    special1 = field(type=bool)
    special2 = field(type=bool)
    score = field(type=int)  # Default score to 0
    def __todict__(self):
        return {
            "num": self.num,
            "uuid": str(self.uuid),
            "c1": str(self.c1),
            "c2": str(self.c2),
            "length": self.length,
            "width": self.width,
            "special1": self.special1,
            "special2": self.special2,
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenLink2(
            num=d["num"],
            uuid=str(d["uuid"]),
            c1=str(d["c1"]),
            c2=str(d["c2"]),
            length=d["length"],
            width=d["width"],
            special1=d["special1"],
            special2=d["special2"],
            score=d["score"],
        )


# Implementing the following Julia function:
# struct ScoreDiff
#     a::Int
#     b::Int
# end
class ScoreDiff(PClass):
    a = field(type=int)
    b = field(type=int)
    def __todict__(self):
        return {
            "a": self.a,
            "b": self.b,
        }
    @staticmethod
    def __fromdict__(d):
        return ScoreDiff(
            a=d["a"],
            b=d["b"]
        )


class RouteStatus(PClass):
    route_uuid = field(type=str)
    completed = field(type=bool)
    def __todict__(self):
        return {
            "route_uuid": self.route_uuid,
            "completed": self.completed,
        }
    @staticmethod
    def __fromdict__(d):
        return RouteStatus(
            route_uuid=d["route_uuid"],
            completed=d["completed"]
        )


# Implementing the following Julia function:
# struct QValueFormula
#     q_num::Union{Nothing,Int}
#     score_diff::ScoreDiff
#     function QValueFormula(formula)
#         new(formula.q_num, ScoreDiff(formula.score_diff...))
#     end
# end
class QValueFormula(PClass):
    q_num = field(type=(int, type(None)), initial=None)  # Union{Nothing,Int}
    score_diff = field(type=ScoreDiff)  # ScoreDiff
    def __todict__(self):
        return {
            "q_num": self.q_num,
            "score_diff": self.score_diff.__todict__()
        }
    @staticmethod
    def __fromdict__(d):
        return QValueFormula(
            q_num=d.get("q_num"),
            score_diff=ScoreDiff.__fromdict__(d["score_diff"])
        )


# Implementing the following Julia function:
# struct QValueTrajectories
#     scores::Vector{Vector{Int}}
#     q_values::Vector{Int}
#     formulas::Vector{QValueFormula}
#     states::Vector{State}
#     actions::Vector{Action}
# end
class QValueTrajectories(PClass):
    scores = field(type=PVector)  # List[List[int]]
    q_values = field(type=PVector)  # List[int]
    formulas = field(type=PVector)  # List[QValueFormula]
    states_no_terminal = field(type=PVector)  # List[State]
    actions = field(type=PVector)  # List[Action]
    def __todict__(self):
        return {
            "scores": list(self.scores),
            "q_values": list(self.q_values),
            "formulas": [f.__todict__() for f in self.formulas],
            "states_no_terminal": [s.__todict__() for s in self.states_no_terminal],
            "actions": [a.__todict__() for a in self.actions],
        }
    @staticmethod
    def __fromdict__(d):
        return QValueTrajectories(
            scores=pvector(d["scores"]),
            q_values=pvector(d["q_values"]),
            formulas=pvector([QValueFormula.__fromdict__(f) for f in d["formulas"]]),
            states_no_terminal=pvector([State.__fromdict__(s) for s in d["states_no_terminal"]]),
            actions=pvector([AltAction.__fromdict__(a) for a in d["actions"]]),
        )



# Implementing the following Julia function:
# struct CapturedPoint
#     player_num::Int
#     point_uuid::UUID
# end
class CapturedPoint(PClass):
    player_num = field(type=int)
    point_uuid = field(type=str)
    def __todict__(self):
        return {
            "player_num": self.player_num,
            "point_uuid": str(self.point_uuid),
        }
    @staticmethod
    def __fromdict__(d):
        return CapturedPoint(
            player_num=d["player_num"],
            point_uuid=d["point_uuid"]
        )


# Implementing the following Julia function:
# struct CapturedSegment
#     player_num::Int
#     segment_uuid::UUID
# end
class CapturedSegment(PClass):
    player_num = field(type=int)
    segment_uuid = field(type=str)
    def __todict__(self):
        return {
            "player_num": self.player_num,
            "segment_uuid": str(self.segment_uuid),
        }
    @staticmethod
    def __fromdict__(d):
        return CapturedSegment(
            player_num=d["player_num"],
            segment_uuid=d["segment_uuid"]
        )


class FrozenPoint2(PClass):
    num = field(type=int)
    uuid = field(type=str)
    def __todict__(self):
        return {
            "num": self.num,
            "uuid": self.uuid,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenPoint2(
            num=d["num"],
            uuid=d["uuid"]
        )


class FrozenCluster(PClass):
    uuid = field(type=str)
    points = field(type=PVector)  # List[UUID]
    score = field(type=int)
    # uuid: UUID
    # points: List[UUID]
    # score: int
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "points": list(self.points),
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenCluster(
            uuid=d["uuid"],
            points=pvector(d["points"]),
            score=d["score"]
        )



# Implementing the following Julia function:
# @kwdef struct FrozenSegment
#     uuid::UUID
#     link_uuid::UUID
#     unit_uuid::Union{Nothing,UUID}
#     path_idx::Int
#     idx::Int
# end
class FrozenSegment(PClass):
    uuid = field(type=str)
    link_uuid = field(type=str)
    unit_uuid = field(type=(str, type(None)), initial=None)
    path_idx = field(type=int)
    idx = field(type=int)
    pieces = field(type=PVector)  # List[Piece]
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "link_uuid": self.link_uuid,
            "unit_uuid": self.unit_uuid,
            "path_idx": self.path_idx,
            "idx": self.idx,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenSegment(
            uuid=d["uuid"],
            link_uuid=d["link_uuid"],
            unit_uuid=d.get("unit_uuid"),  # Handle None case
            path_idx=d["path_idx"],
            idx=d["idx"],
        )


# Implementing the following Julia function:
# struct OrderedSegment
#     path_segment_num::Int
#     segment
# end
class OrderedSegment(PClass):
    path_segment_num = field(type=int)
    segment = field(type=FrozenSegment)  # UUID
    def __todict__(self):
        return {
            "path_segment_num": self.path_segment_num,
            "segment": self.segment.__todict__(),
        }
    @staticmethod
    def __fromdict__(d):
        return OrderedSegment(
            path_segment_num=d["path_segment_num"],
            segment=FrozenSegment.__fromdict__(d["segment"])
        )


# Implementing the following Julia function:
# struct SegmentStatus
#     path_num::Int
#     path_segment_num::Int
#     captured_by_me::Bool
#     captured_by_other::Bool
#     available_to_me::Bool
#     status::String
#     segment
# end
class SegmentStatus(PClass):
    path_idx = field(type=int)
    path_num = field(type=int)
    path_segment_num = field(type=int)
    captured_by_me = field(type=bool)
    captured_by_other = field(type=bool)
    available_to_me = field(type=bool)
    status = field(type=str)
    segment = field(type=FrozenSegment)  # UUID
    def __todict__(self):
        return {
            "path_idx": self.path_idx,
            "path_num": self.path_num,
            "path_segment_num": self.path_segment_num,
            "captured_by_me": self.captured_by_me,
            "captured_by_other": self.captured_by_other,
            "available_to_me": self.available_to_me,
            "status": self.status,
            "segment": self.segment.__todict__(),
        }
    @staticmethod
    def __fromdict__(d):
        return SegmentStatus(
            path_idx=d["path_idx"],
            path_num=d["path_num"],
            path_segment_num=d["path_segment_num"],
            captured_by_me=d["captured_by_me"],
            captured_by_other=d["captured_by_other"],
            available_to_me=d["available_to_me"],
            status=d["status"],
            segment=FrozenSegment.__fromdict__(d["segment"])
        )


# Implementing the following Julia function:
# struct OrderedFullfillment
#     segment_num::Int
#     unit_card_num::Int
# end
class OrderedFullfillment(PClass):
    segment_num = field(type=int)
    unit_card_num = field(type=int)
    def __todict__(self):
        return {
            "segment_num": self.segment_num,
            "unit_card_num": self.unit_card_num,
        }
    @staticmethod
    def __fromdict__(d):
        return OrderedFullfillment(
            segment_num=d["segment_num"],
            unit_card_num=d["unit_card_num"]
        )

# Implementing the following Julia function:
# struct PathStatus
#     num::Int
#     fulfillable::Bool
#     segment_statuses::Vector{SegmentStatus}
#     sample_fulfillment::Vector{OrderedFullfillment}
# end
class PathStatus(PClass):
    idx = field(type=int)
    num = field(type=int)
    fulfillable = field(type=bool)
    segment_statuses = field(type=PVector)  # List[SegmentStatus]
    sample_fulfillment = field(type=PVector)  # List[OrderedFullfillment]
    def __todict__(self):
        return {
            "idx": self.idx,
            "num": self.num,
            "fulfillable": self.fulfillable,
            "segment_statuses": [x.__todict__() for x in self.segment_statuses],
            "sample_fulfillment": [x.__todict__() for x in self.sample_fulfillment],
        }
    @staticmethod
    def __fromdict__(d):
        return PathStatus(
            idx=d["idx"],
            num=d["num"],
            fulfillable=d["fulfillable"],
            segment_statuses=pvector([SegmentStatus.__fromdict__(x) for x in d["segment_statuses"]]),
            sample_fulfillment=pvector([OrderedSegment.__fromdict__(x) for x in d["sample_fulfillment"]])
        )


# Implementing the following Julia function:
# @kwdef struct FrozenLinkPath
#     is_mixed::Bool
#     segments::Vector{FrozenSegment}
# end
class FrozenLinkPath(PClass):
    is_mixed = field(type=bool)
    segments = field(type=PVector)  # List[FrozenSegment]
    def __todict__(self):
        return {
            "is_mixed": self.is_mixed,
            "segments": [x.__todict__() for x in self.segments],
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenLinkPath(
            is_mixed=d["is_mixed"],
            segments=pvector([FrozenSegment.__fromdict__(x) for x in d["segments"]])
        )


class FrozenPath(PClass):
    num = field(type=int)
    link_num = field(type=int)
    start_point_uuid = field(type=str)
    end_point_uuid = field(type=str)
    start_point_num = field(type=int)
    end_point_num = field(type=int)
    path = field(type=FrozenLinkPath)
    def __todict__(self):
        return {
            "num": self.num,
            "link_num": self.link_num,
            "start_point_uuid": self.start_point_uuid,
            "end_point_uuid": self.end_point_uuid,
            "start_point_num": self.start_point_num,
            "end_point_num": self.end_point_num,
            "path": self.path.__todict__(),
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenPath(
            num=d["num"],
            link_num=d["link_num"],
            start_point_uuid=d["start_point_uuid"],
            end_point_uuid=d["end_point_uuid"],
            start_point_num=d["start_point_num"],
            end_point_num=d["end_point_num"],
            path=FrozenLinkPath.__fromdict__(d["path"])
        )


class FrozenSetting(PClass):
    name = field(type=str)
    value_json = field(type=str)
    # name: str
    # value_json: str
    def __todict__(self):
        return {
            "name": self.name,
            "value_json": self.value_json,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenSetting(
            name=d["name"],
            value_json=d["value_json"]
        )


class FrozenDeckUnit2(PClass):
    num = field(type=int)
    quantity = field(type=int)
    is_wild = field(type=bool)
    unit_uuid = field(type=str)
    def __todict__(self):
        return {
            "num": self.num,
            "quantity": self.quantity,
            "is_wild": self.is_wild,
            "unit_uuid": self.unit_uuid,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenDeckUnit2(
            num=d["num"],
            quantity=d["quantity"],
            is_wild=d["is_wild"],
            unit_uuid=d["unit_uuid"]
        )


class FrozenRoute(PClass):
    num = field(type=int)
    uuid = field(type=str)
    point_a_uuid = field(type=str)
    point_b_uuid = field(type=str)
    score = field(type=int)
    start_num = field(type=int)
    end_num = field(type=int)
    def __todict__(self):
        return {
            "num": self.num,
            "uuid": self.uuid,
            "point_a_uuid": self.point_a_uuid,
            "point_b_uuid": self.point_b_uuid,
            "score": self.score,
            "start_num": self.start_num,
            "end_num": self.end_num,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenRoute(
            num=d["num"],
            uuid=d["uuid"],
            point_a_uuid=d["point_a_uuid"],
            point_b_uuid=d["point_b_uuid"],
            score=d["score"],
            start_num=d["start_num"],
            end_num=d["end_num"]
        )


class FrozenPieceTemplate(PClass):
    uuid = field(type=str)
    idx = field(type=int)
    has_player = field(type=bool)
    quantity = field(type=int)
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "idx": self.idx,
            "has_player": self.has_player,
            "quantity": self.quantity,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenPieceTemplate(
            uuid=d["uuid"],
            idx=d["idx"],
            has_player=d["has_player"],
            quantity=d["quantity"],
        )
    

class FrozenDekCard(PClass):
    uuid = field(type=str)
    idx = field(type=int)
    quantity = field(type=int)
    resource_uuid = field(type=(str, type(None)), initial=None)
    goal_uuid = field(type=(str, type(None)), initial=None)
    is_wild = field(type=bool)
    dek_uuid = field(type=str)
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "idx": self.idx,
            "quantity": self.quantity,
            "resource_uuid": self.resource_uuid,
            "goal_uuid": self.goal_uuid,
            "is_wild": self.is_wild,
            "dek_uuid": self.dek_uuid
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenDekCard(
            uuid=d["uuid"],
            idx=d["idx"],
            quantity=d["quantity"],
            resource_uuid=d["resource_uuid"],
            goal_uuid=d["goal_uuid"],
            is_wild=d["is_wild"],
            dek_uuid=d["dek_uuid"]
        )


class FrozenDek(PClass):
    uuid = field(type=str)
    idx = field(type=int)
    dek_cards = field(type=PVector)  # List[FrozenDekCard]
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "idx": self.idx,
            "dek_cards": [card.__todict__() for card in self.dek_cards],
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenDek(
            uuid=d["uuid"],
            idx=d["idx"],
            dek_cards=pvector([FrozenDekCard.__fromdict__(card) for card in d["dek_cards"]]),
        )
    

class FrozenBonus(PClass):
    uuid = field(type=str)
    code = field(type=str)
    score = field(type=int)
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "code": self.code,
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenBonus(
            uuid=d["uuid"],
            code=d["code"],
            score=d["score"],
        )


class FrozenGoal(PClass):
    uuid = field(type=str)
    description = field(type=(str, type(None)), initial=None)
    node_uuids = field(type=(list, type(None)), initial=None)  # List[str]
    edge_uuids = field(type=(list, type(None)), initial=None)
    region_uuids = field(type=(list, type(None)), initial=None)
    score = field(type=int)
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "node_uuids": self.node_uuids,
            "edge_uuids": self.edge_uuids,
            "region_uuids": self.region_uuids,
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenGoal(
            uuid=d["uuid"],
            node_uuids=d["node_uuids"],
            edge_uuids=d["edge_uuids"],
            region_uuids=d["region_uuids"],
            score=d["score"]
        )


class FrozenBoardConfig(PClass):
    bonuses = field(type=PVector)  # List[FrozenBonus]
    goals = field(type=PVector)  # List[FrozenGoal]
    deks = field(type=PVector)  # List[FrozenDek]
    piece_templates = field(type=PVector)  # List[FrozenPieceTemplate]
    routes = field(type=PVector)  # List[FrozenRoute]
    deck_units = field(type=PVector)  # List[FrozenDeckUnit2]
    settings = field(type=PVector)  # List[FrozenSetting]
    points = field(type=PVector)  # List[FrozenPoint2]
    clusters = field(type=PVector)  # List[FrozenCluster]
    board_paths = field(type=PVector)  # List[FrozenPath]
    len_scores = field(type=PVector)  # List[FrozenLenScore]
    links = field(type=PVector)  # List[FrozenLink2]
    hooks = field(type=PVector)  # List[Hook]
    def __todict__(self):
        return {
            "bonuses": [b.__todict__() for b in self.bonuses],
            "goals": [g.__todict__() for g in self.goals],
            "deks": [d.__todict__() for d in self.deks],
            "piece_templates": [x.__todict__() for x in self.piece_templates],
            "routes": [x.__todict__() for x in self.routes],
            "deck_units": [x.__todict__() for x in self.deck_units],
            "settings": [x.__todict__() for x in self.settings],
            "points": [x.__todict__() for x in self.points],
            "clusters": [x.__todict__() for x in self.clusters],
            "board_paths": [x.__todict__() for x in self.board_paths],
            "len_scores": [x.__todict__() for x in self.len_scores],
            "links": [x.__todict__() for x in self.links],
            "hooks": [x.__todict__() for x in self.hooks],
        }
    @staticmethod
    def __fromdict__(d):
        return FrozenBoardConfig(
            bonuses=pvector([FrozenBonus.__fromdict__(x) for x in d['bonuses']]),
            goals=pvector([FrozenGoal.__fromdict__(x) for x in d['goals']]),
            deks=pvector([FrozenDek.__fromdict__(x) for x in d['deks']]),
            piece_templates=pvector([FrozenPieceTemplate.__fromdict__(x) for x in d['piece_templates']]),
            routes = initfrozenroutes(d),
            deck_units = getdeckunits(d['deck_units']),
            settings = getsettings(d['settings']),
            points = getpoints(d["points"]),
            clusters = getclusters(d["clusters"]),
            board_paths = getboardpaths(d["board_paths"]),
            len_scores=pvector([FrozenLenScore.__fromdict__(x) for x in d['len_scores']]),
            links=pvector([FrozenLink2.__fromdict__(x) for x in d['links']]),
            hooks=pvector([Hook.__fromdict__(x) for x in d.get('hooks', [])])
        )


@dispatch(dict)
def initboardconfig(d):
    return FrozenBoardConfig.__fromdict__(d)


class StaticBoardConfig(PClass):
    uuid = field(type=str)
    board_config = field(type=FrozenBoardConfig)
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "board_config": self.board_config.__todict__()
        }
    @staticmethod
    def __fromdict__(d):
        return StaticBoardConfig(
            uuid=d["uuid"],
            board_config=FrozenBoardConfig.__fromdict__(d["board_config"])
        )


@dispatch(dict)
def initfrozenroutes(d):
    pointuuids2nums = {p['uuid']: n for n, p in enumerate(d['points'])}
    return pvector([
        FrozenRoute(
            num=i+1,
            uuid=r['uuid'],
            point_a_uuid=r['point_a_uuid'],
            point_b_uuid=r['point_b_uuid'],
            score=r['score'],
            start_num=pointuuids2nums[r['point_a_uuid']],
            end_num=pointuuids2nums[r['point_b_uuid']],
        )
        for i, r in enumerate(d['routes'])
    ])


MAX_PATH_LENGTH = 100

# Implementing the following Julia function:
# function getfrozenpathscores(b::FrozenBoardConfig)
#     d = Dict()
#     for x in b.len_scores
#         d[x.len] = x.score
#     end
#     [get(d, i, 0) for i in collect(1:MAX_PATH_LENGTH)]
# end
@dispatch(FrozenBoardConfig)
def getfrozenpathscores(b):
    d = {x.length: x.score for x in b.len_scores}
    return [d.get(i, 0) for i in range(1, MAX_PATH_LENGTH + 1)]


# Sample json data
# {"board_paths": [
#         {
#             "num": 1,
#             "path": {
#                 "is_mixed": false,
#                 "segments": [
#                     {
#                         "idx": 0,
#                         "uuid": "54fe6576-13a1-445a-ba19-dd1809798cea",
#                         "path_idx": 0,
#                         "link_uuid": "0e90684e-d9ab-4d31-bb12-33ab4e11c91a",
#                         "unit_uuid": null
#                     }
#                 ]
#             },
#             "link_num": 1,
#             "end_point_num": 6,
#             "start_point_num": 8
#         },
# ]}
def getboardpaths(d):
    return pvector([
        FrozenPath(
            num=x['num'],
            link_num=x['link_num'],
            start_point_uuid=x['start_point_uuid'],
            end_point_uuid=x['end_point_uuid'],
            start_point_num=x['start_point_num'],
            end_point_num=x['end_point_num'],
            path=getlinkpath(x['path']),
        )
        for x in d
    ])


def getlinkpath(d):
    return FrozenLinkPath(
        is_mixed=d['is_mixed'],
        segments=pvector(getsegments(d['segments'])),
    )


def getsegments(d):
    return [
        FrozenSegment(
            idx=x['idx'],
            uuid=x['uuid'],
            path_idx=x['path_idx'],
            link_uuid=x['link_uuid'],
            unit_uuid=x['unit_uuid'],
        )
        for x in d
    ]


def getclusters(d):
    return pvector([
        FrozenCluster(
            uuid=x['uuid'],
            points=pvector([p for p in x['points']]),
            score=x['score'],
        )
        for n, x in enumerate(d)
    ])


def getpoints(d):
    return pvector([
        FrozenPoint2(
            num=n,
            uuid=x['uuid'],
        )
        for n, x in enumerate(d)
    ])

def getsettings(d):
    return pvector([
        BoardSetting(
            name=x['name'],
            value_json=x['value_json'],
        )
        for n, x in enumerate(d)
    ])


def getdeckunits(d):
    return pvector([
        FrozenDeckUnit2(
            num=x['num'],
            quantity=x['quantity'],
            is_wild=x['is_wild'],
            unit_uuid=x['unit_uuid']
        )
        for n, x in enumerate(d)
    ])


class BoardSetting(PClass):
    name = field(type=str)
    value_json = field(type=str)
    def __todict__(self):
        return {
            "name": self.name,
            "value_json": self.value_json,
        }


class Card(PClass):
    idx = field(type=int)
    deck_idx = field(type=int)
    name = field(type=str)
    is_wild = field(type=bool)
    resource_idx = field(type=(int, type(None)), initial=None)
    resource_uuid = field(type=(str, type(None)), initial=None)
    goal_idx = field(type=(int, type(None)), initial=None)
    goal_uuid = field(type=(str, type(None)), initial=None)
    def to_llm_dict(self):
        return {
            "name": self.name,
            "is_wild": self.is_wild,
            "resource": f"resource-{self.resource_idx}" if self.resource_idx is not None else None,
            "goal": f"goal-{self.goal_idx}" if self.goal_idx is not None else None,
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "deck_idx": self.deck_idx,
            "name": self.name,
            "is_wild": self.is_wild,
            "resource_idx": self.resource_idx,
            "resource_uuid": self.resource_uuid,
            "goal_idx": self.goal_idx,
            "goal_uuid": self.goal_uuid,
        }
    @staticmethod
    def __fromdict__(d):
        return Card(
            idx=d["idx"],
            deck_idx=d["deck_idx"],
            name=d["name"],
            is_wild=d["is_wild"],
            resource_idx=d["resource_idx"],
            resource_uuid=d["resource_uuid"],
            goal_idx=d["goal_idx"],
            goal_uuid=d["goal_uuid"],
        )


class Unit(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    is_wild = field(type=bool)
    def to_llm_dict(self):
        return {
            "name": f"resource-{self.idx}",
            "is_wild": self.is_wild,
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "is_wild": self.is_wild,
        }
    @staticmethod
    def __fromdict__(d):
        return Unit(
            idx=d["idx"],
            uuid=d["uuid"],
            is_wild=d["is_wild"],
        )



class Fig(PClass):
    # TODO: the two fields below should just be a "StaticBoardConfig" object
    static_board_config_uuid = field(type=str)
    board_config = field(type=FrozenBoardConfig)
    nodes= field(type=PVector)  # List[Node]
    edges= field(type=PVector)  # List[Edge]
    paths= field(type=PVector)  # List[FrozenPath]
    segments= field(type=PVector)  # List[Segment]
    resources= field(type=PVector)  # List[Unit]
    goals = field(type=PVector)  # List[Goal]
    nodeuuid2idx = field(type=dict)  # Dict[str, int]
    edgetuple2idx = field(type=dict)  # Dict[Tuple[int, int], int]
    bonusuuid2bonusidx = field(type=dict)  # Dict[str, int]
    resourceuuid2idx = field(type=dict)  # Dict[str, int]
    goaluuid2idx = field(type=dict)  # Dict[str, int]
    def to_llm_dict(self):
        return {
            "nodes": [x.to_llm_dict() for x in self.nodes],
            "edges": [x.to_llm_dict() for x in self.edges],
            "resources": [x.to_llm_dict() for x in self.resources],
            "goals": [x.to_llm_dict() for x in self.goals],
            # "adjacency_matrix": [[1, 0, 1]],
        }
    def __todict__(self):
        return {
            "static_board_config_uuid": self.static_board_config_uuid,
            "board_config": self.board_config.__todict__(),
            "nodes": [node.__todict__() for node in self.nodes],
            "edges": [edge.__todict__() for edge in self.edges],
            "paths": [path.__todict__() for path in self.paths],
            "segments": [segment.__todict__() for segment in self.segments],
            "resources": [x.__todict__() for x in self.resources],
            "goals": [x.__todict__() for x in self.goals],
            "nodeuuid2idx": self.nodeuuid2idx,
            "edgetuple2idx": [{"k": list(k), "v": v} for k, v in self.edgetuple2idx.items()],
            "bonusuuid2bonusidx": self.bonusuuid2bonusidx,
            "resourceuuid2idx": self.resourceuuid2idx,
            "goaluuid2idx": self.goaluuid2idx,
        }
    @staticmethod
    def __fromdict__(d):
        return Fig(
            static_board_config_uuid=d["static_board_config_uuid"], 
            board_config=FrozenBoardConfig.__fromdict__(d["board_config"]),
            nodes=pvector([Node.__fromdict__(node) for node in d["nodes"]]),
            edges=pvector([Edge.__fromdict__(edge) for edge in d["edges"]]),
            paths=pvector([FrozenPath.__fromdict__(path) for path in d["paths"]]),
            segments=pvector([Segment.__fromdict__(segment) for segment in d["segments"]]),
            resources=pvector([Unit.__fromdict__(x) for x in d["resources"]]),
            goals=pvector([Goal.__fromdict__(x) for x in d["goals"]]),
            nodeuuid2idx=d["nodeuuid2idx"],
            edgetuple2idx={tuple(item["k"]): item["v"] for item in d["edgetuple2idx"]},
            bonusuuid2bonusidx=d["bonusuuid2bonusidx"],
            resourceuuid2idx=d["resourceuuid2idx"],
            goaluuid2idx=d["goaluuid2idx"],
        )
    
    
@dispatch(FrozenBoardConfig, dict)
def get_goals(board_config, nodeuuid2idx):
    frozen_goals = board_config.goals
    goals = []
    for idx, x in enumerate(frozen_goals):
        node_names = None
        edge_names = None
        region_names = None
        if x.node_uuids is not None:
            node_names = pvector([f"node-{nodeuuid2idx[nu]}" for nu in x.node_uuids])
        goal = Goal(
            idx=idx,
            uuid=x.uuid,
            name=f"goal-{idx}",
            score=x.score,
            node_uuids=pvector(x.node_uuids) if x.node_uuids is not None else None,
            node_names=node_names,
            edge_names=edge_names,
            region_names=region_names,
        )
        goals.append(goal)
    return pvector(goals)


@dispatch(str, FrozenBoardConfig)
def initfig(static_board_config_uuid, board_config):

    nodes = get_nodes(board_config)
    nodeuuid2idx = {node.uuid: idx for idx, node in enumerate(nodes)}

    goals = get_goals(board_config, nodeuuid2idx)
    goaluuid2idx = {goal.uuid: idx for idx, goal in enumerate(goals)}

    all_resources = {}
    for deck_unit in board_config.deck_units:
        all_resources[deck_unit.unit_uuid] = deck_unit
    # sort all_resources to have a consistent ordering
    resources = [
        Unit(
            idx=idx,
            uuid=res_uuid,
            is_wild=all_resources[res_uuid].is_wild,
        )
        for idx, res_uuid in enumerate(sorted(all_resources.keys()))
    ]
    resourceuuid2idx = {resource.uuid: idx for idx, resource in enumerate(resources)}

    edges = get_edges(board_config, nodeuuid2idx, resourceuuid2idx)
    bonusuuid2bonusidx = {bonus.uuid: idx for idx, bonus in enumerate(board_config.bonuses)}

    edgetuple2idx = {}
    for edge in edges:
        node_1_idx = nodeuuid2idx[edge.node_1_uuid]
        node_2_idx = nodeuuid2idx[edge.node_2_uuid]
        edge_tuple = (min(node_1_idx, node_2_idx), max(node_1_idx, node_2_idx))
        edgetuple2idx[edge_tuple] = edge.idx
        
    paths = v()
    for edge in edges:
        for path in edge.paths:
            paths = paths.append(path)

    return Fig(
        static_board_config_uuid=static_board_config_uuid,
        board_config=board_config,
        nodes=nodes,
        nodeuuid2idx=nodeuuid2idx,
        edges=edges,
        edgetuple2idx=edgetuple2idx,
        paths=paths,
        segments=get_segments(edges),
        goals=goals,
        bonusuuid2bonusidx=bonusuuid2bonusidx,
        resources=pvector(resources),
        resourceuuid2idx=resourceuuid2idx,
        goaluuid2idx=goaluuid2idx,
    )


class PublicGameConfig(PClass):
    uuid = field(type=str)
    started_at = field(type=str)
    num_players = field(type=int)
    fig = field(type=Fig)
    starting_decks = field(type=PVector)  # List[Deck]
    starting_piles = field(type=PVector) # List[Pile]
    wild_unit_uuids = field(type=PVector)  # List[str]
    def to_llm_dict(self):
        return {
            "num_players":  self.num_players,
            "starting_piles": [x.to_llm_dict() for x in self.starting_piles],
            "starting_decks": [x.to_llm_dict() for x in self.starting_decks],
            "goals": [x.to_llm_dict() for x in self.fig.goals],
            "resources": [x.to_llm_dict() for x in self.fig.resources],
        }
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "started_at": self.started_at,
            "num_players": self.num_players,
            "fig": self.fig.__todict__(),
            "starting_decks": [d.__todict__() for d in self.starting_decks],
            "starting_piles": [pile.__todict__() for pile in self.starting_piles],
            "wild_unit_uuids": list(self.wild_unit_uuids),
        }
    @staticmethod
    def __fromdict__(d):
        return PublicGameConfig(
            uuid=d["uuid"],
            started_at=d["started_at"],
            num_players=d["num_players"],
            fig=Fig.__fromdict__(d["fig"]),
            starting_decks=pvector([Deck.__fromdict__(deck) for deck in d["starting_decks"]]),
            starting_piles=pvector([Pile.__fromdict__(x) for x in d["starting_piles"]]),
            wild_unit_uuids=pvector(d["wild_unit_uuids"]),
        )


class GameConfig(PClass):
    seed = field(type=int)
    uuid = field(type=str)
    started_at = field(type=str)
    num_players = field(type=int)
    fig = field(type=Fig)
    starting_decks = field(type=PVector)  # List[Deck]
    starting_piles = field(type=PVector) # List[Pile]
    wild_unit_uuids = field(type=PVector)  # List[str]
    def to_llm_dict(self):
        return {
            "all_piles": [x.to_llm_dict() for x in self.starting_piles],
            "all_decks": [x.to_llm_dict() for x in self.starting_decks],
            "resources": [x.to_llm_dict() for x in self.fig.resources],
            "goals": [x.to_llm_dict() for x in self.fig.goals],
        }
    def __todict__(self):
        return {
            "seed": self.seed,
            "uuid": self.uuid,
            "started_at": self.started_at,
            "num_players": self.num_players,
            "fig": self.fig.__todict__(),
            "starting_decks": [d.__todict__() for d in self.starting_decks],
            "starting_piles": [pile.__todict__() for pile in self.starting_piles],
            "wild_unit_uuids": list(self.wild_unit_uuids),
        }
    @staticmethod
    def __fromdict__(d):
        return GameConfig(
            seed=d["seed"],
            uuid=d["uuid"],
            started_at=d["started_at"],
            num_players=d["num_players"],
            fig=Fig.__fromdict__(d["fig"]),
            starting_decks=pvector([Deck.__fromdict__(deck) for deck in d["starting_decks"]]),
            starting_piles=pvector([Pile.__fromdict__(x) for x in d["starting_piles"]]),
            wild_unit_uuids=pvector(d["wild_unit_uuids"]),
        )


@dispatch(GameConfig)
def getpublicgameconfig(game_config):
    return PublicGameConfig(
        uuid=game_config.uuid,
        started_at=game_config.started_at,
        num_players=game_config.num_players,
        fig=game_config.fig,
        starting_decks=game_config.starting_decks,
        starting_piles=game_config.starting_piles,
        wild_unit_uuids=game_config.wild_unit_uuids,
    )


@dispatch(PublicGameConfig)
def getgameconfig(public_game_config):
    return GameConfig(
        seed=random.randint(0, 2**31 - 1),
        uuid=public_game_config.uuid,
        started_at=public_game_config.started_at,
        num_players=public_game_config.num_players,
        fig=public_game_config.fig,
        starting_decks=public_game_config.starting_decks,
        starting_piles=public_game_config.starting_piles,
        wild_unit_uuids=public_game_config.wild_unit_uuids,
    )


class PlayerGraph(PClass):
    player_idx = field(type=int)
    neighbors = field(type=PVector)  # PVector[PVector[int]]
    claimed_edges_adjacency_matrix = field(type=PVector)  # PVector[PVector[int]]
    def to_llm_dict(self):
        return {
            "claimed_edges_adjacency_matrix": list(self.claimed_edges_adjacency_matrix),
        }
    def __todict__(self):
        return {
            "player_idx": self.player_idx,
            "neighbors": [list(x) for x in self.neighbors],
            "claimed_edges_adjacency_matrix": [list(x) for x in self.claimed_edges_adjacency_matrix],
        }
    @staticmethod
    def __fromdict__(d):
        return PlayerGraph(
            player_idx=d["player_idx"],
            neighbors=pvector(d["neighbors"]),
            claimed_edges_adjacency_matrix=pvector(d["claimed_edges_adjacency_matrix"])
        )


class PublicPlayer(PClass):
    idx = field(type=int)
    pieces = field(type=PVector)  # List[str]
    deck_counts = field(type=PVector)
    discard_deck_counts = field(type=PVector)
    piece_template_counts = field(type=PVector)
    graph = field(type=PlayerGraph)
    def to_llm_dict(self):
        return {
            "player_idx": self.idx,
            "pieces": list(self.pieces),
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "pieces": list(self.pieces),
            "deck_counts": list(self.deck_counts),
            "discard_deck_counts": list(self.discard_deck_counts),
            "piece_template_counts": list(self.piece_template_counts),
            "graph": self.graph.__todict__(),
        }
    @staticmethod
    def __fromdict__(d):
        return PublicPlayer(
            idx=d["idx"],
            pieces=pvector(d["pieces"]),
            deck_counts=list(d["deck_counts"]),
            discard_deck_counts=list(d["discard_deck_counts"]),
            piece_template_counts=list(d["piece_template_counts"]),
            graph=PlayerGraph.__fromdict__(d["graph"]),
        )


class PlayerScore2(PClass):
    public_items = field(type=PVector)  # List[ScoreItem]
    private_items = field(type=PVector)  # List[ScoreItem]
    def __todict__(self):
        return {
            "public_items": [x.__todict__() for x in self.public_items], 
            "private_items": [x.__todict__() for x in self.private_items],
        }
    @staticmethod
    def __fromdict__(d):
        return PlayerScore2(
            public_items=pvector([ScoreItem.__fromdict__(x) for x in d["public_items"]]),
            private_items=pvector([ScoreItem.__fromdict__(x) for x in d["private_items"]]),
        )


class Player(PClass):
    idx = field(type=int)
    pieces = field(type=PVector)  # List[str]
    cards = field(type=PVector)  # List[str]
    discard_tray = field(type=PVector)  # PVector[str]
    graph = field(type=PlayerGraph)
    score = field(type=PlayerScore2)
    def to_llm_dict(self):
        # [
        #     {
        #         "player_idx": 0,
        #         "claimed_edges_adjacency_matrix": [
        #             [0, 1, 0, 1],
        #             [1, 0, 1, 0],
        #             [0, 1, 0, 1],
        #             [1, 0, 1, 0],
        #         ],
        #         "scoring_items": 45,
        #         "piece_names": [],
        #     }
        # ]
        return {
            "player_idx": self.idx,
            "pieces": list(self.pieces),
            "graph": self.graph.to_llm_dict(),
            "score": self.score.__todict__(),
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "pieces": list(self.pieces),
            "cards": list(self.cards),
            "discard_tray": list(self.discard_tray),
            "graph": self.graph.__todict__(),
            "score": self.score.__todict__(),
        }
    @staticmethod
    def __fromdict__(d):
        return Player(
            idx=d["idx"],
            pieces=pvector(d["pieces"]),
            cards=pvector(d["cards"]),
            discard_tray=pvector(d["discard_tray"]),
            graph=PlayerGraph.__fromdict__(d["graph"]),
            score=PlayerScore2.__fromdict__(d["score"])
        )


class GoalCompletion(PClass):
    goal_idx = field(type=int)
    goal_uuid = field(type=str)
    complete = field(type=bool, initial=False)
    def __todict__(self):
        return {
            "goal_idx": self.goal_idx,
            "goal_uuid": self.goal_uuid,
            "complete": self.complete,
        }
    @staticmethod
    def __fromdict__(d):
        return GoalCompletion(
            goal_idx=d["goal_idx"],
            goal_uuid=d["goal_uuid"],
            complete=d.get("complete")
        )


class PlayerNode(PClass):
    player_idx = field(type=int)
    node_idx = field(type=int)
    neighbors = field(type=PVector)  # List[int]
    def __todict__(self):
        return {
            "player_idx": self.player_idx,
            "node_idx": self.node_idx,
            "neighbors": list(self.neighbors),
        }
    @staticmethod
    def __fromdict__(d):
        return PlayerNode(
            player_idx=d["player_idx"],
            node_idx=d["node_idx"],
            neighbors=pvector(d["neighbors"])
        )


class PrivatePlayerScore(PClass):
    items = field(type=PVector)  # List[ScoreItem]
    total = field(type=int)
    def to_llm_dict(self):
        return {
            "items": [x.to_llm_dict() for x in self.items],
            "total": self.total,
        }
    def __todict__(self):
        return {
            "items": [x.__todict__() for x in self.items], 
            "total": self.total,
        }
    @staticmethod
    def __fromdict__(d):
        return PrivatePlayerScore(
            items=pvector([ScoreItem.__fromdict__(x) for x in d["items"]]),
            total=d["total"]
        )


class PrivateState(PClass):
    my_history = field(type=PVector)  # List[Action2]
    player_score = field(type=PrivatePlayerScore)
    player = field(type=Player)
    legal_actions = field(type=PVector)  # List[LegalAction]
    goal_completions = field(type=PVector)  # List[GoalCompletion]
    def to_llm_dict(self):
        return {
            "cards": list(self.player.cards),
            "discard_tray": list(self.player.discard_tray),
            "player_score": self.player_score.to_llm_dict(),
            "legal_actions": [x.to_llm_dict() for x in self.legal_actions],
        }
    def __todict__(self):
        return {
            "my_history": [x.__todict__() for x in self.my_history],
            "player_score": self.player_score.__todict__(),
            "player": self.player.__todict__(),
            "legal_actions": [x.__todict__() for x in self.legal_actions],
            "goal_completions": [x.__todict__() for x in self.goal_completions],
        }
    @staticmethod
    def __fromdict__(d):
        return PrivateState(
            my_history=pvector([Action2.__fromdict__(x) for x in d["my_history"]]),
            player_score=PrivatePlayerScore.__fromdict__(d["player_score"]),
            player=Player.__fromdict__(d["player"]),
            legal_actions=pvector([LegalAction.__fromdict__(x) for x in d["legal_actions"]]),
            goal_completions=pvector([GoalCompletion.__fromdict__(x) for x in d["goal_completions"]]),
        )


class FaceupCardStack(PClass):
    cards = field(type=PVector)  # List[str]
    def to_llm_dict(self):
        return {
            "cards": list(self.cards),
        }
    def __todict__(self):
        return {
            "cards": list(self.cards),
        }
    @staticmethod
    def __fromdict__(d):
        return FaceupCardStack(
            cards=pvector(d["cards"]),
        )


class FacedownCardStack(PClass):
    cards = field(type=PVector)  # List[str]
    def __todict__(self):
        return {
            "cards": list(self.cards),
        }
    @staticmethod
    def __fromdict__(d):
        return FaceupCardStack(
            cards=pvector(d["cards"]),
        )


class PublicFacedownCardStack(PClass):
    num_cards = field(type=int)
    def to_llm_dict(self):
        return {
            "num_cards": self.num_cards,
        }
    def __todict__(self):
        return {
            "num_cards": self.num_cards,
        }
    @staticmethod
    def __fromdict__(d):
        return PublicFacedownCardStack(
            num_cards=d["num_cards"],
        )


class FaceupCardSpread(PClass):
    spots = field(type=PVector)  # List[Card|None]
    def to_llm_dict(self):
        return {
            "spots": list(self.spots),
        }
    def __todict__(self):
        return {
            "spots": list(self.spots),
        }
    @staticmethod
    def __fromdict__(d):
        return FaceupCardSpread(
            spots=pvector(d["spots"]),
        )


class FacedownCardSpread(PClass):
    spots = field(type=PVector)  # List[Card|None]
    def __todict__(self):
        return {
            "spots": list(self.spots),
        }
    @staticmethod
    def __fromdict__(d):
        return FacedownCardSpread(
            spots=pvector(d["spots"]),
        )


class PublicFacedownCardSpread(PClass):
    spots = field(type=PVector)  # List[bool]  # True if card is present, False if empty
    def to_llm_dict(self):
        return {
            "spots": list(self.spots),
        }
    def __todict__(self):
        return {
            "spots": list(self.spots),
        }
    @staticmethod
    def __fromdict__(d):
        return PublicFacedownCardSpread(
            spots=pvector(d["spots"]),
        )


class PublicDeck(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    cards = field(type=PVector)  # PVector[Card]
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            'cards': [card.__todict__() for card in self.cards],
        }
    @staticmethod
    def __fromdict__(d):
        return PublicDeck(
            idx=d["idx"],
            uuid=d["uuid"],
            cards=pvector([Card.__fromdict__(card) for card in d["cards"]]),
        )


class PublicDeckStatus(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    faceup_stack = field(type=(FaceupCardStack, type(None)), initial=None)
    faceup_spread = field(type=(FaceupCardSpread, type(None)), initial=None)
    facedown_stack = field(type=(PublicFacedownCardStack, type(None)), initial=None)
    facedown_spread = field(type=(PublicFacedownCardSpread, type(None)), initial=None)
    discard_faceup_stack = field(type=(FaceupCardStack, type(None)), initial=None)
    discard_facedown_stack = field(type=(PublicFacedownCardStack, type(None)), initial=None)
    def to_llm_dict(self):
        return {
            "name": f"deck-{self.idx}",
            "faceup_stack": self.faceup_stack.to_llm_dict() if self.faceup_stack else None,
            "faceup_spread": self.faceup_spread.to_llm_dict() if self.faceup_spread else None,
            "facedown_stack": self.facedown_stack.to_llm_dict() if self.facedown_stack else None,
            "facedown_spread": self.facedown_spread.to_llm_dict() if self.facedown_spread else None,
            "discard_faceup_stack": self.discard_faceup_stack.to_llm_dict() if self.discard_faceup_stack else None,
            "discard_facedown_stack": self.discard_facedown_stack.to_llm_dict() if self.discard_facedown_stack else None,
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "faceup_stack": self.faceup_stack.__todict__() if self.faceup_stack else None,
            "faceup_spread": self.faceup_spread.__todict__() if self.faceup_spread else None,
            "facedown_stack": self.facedown_stack.__todict__() if self.facedown_stack else None,
            "facedown_spread": self.facedown_spread.__todict__() if self.facedown_spread else None,
            "discard_faceup_stack": self.discard_faceup_stack.__todict__() if self.discard_faceup_stack else None,
            "discard_facedown_stack": self.discard_facedown_stack.__todict__() if self.discard_facedown_stack else None,
        }
    @staticmethod
    def __fromdict__(d):
        return PublicDeckStatus(
            idx=d["idx"],
            uuid=d["uuid"],
            faceup_stack=FaceupCardStack.__fromdict__(d["faceup_stack"]) if d.get("faceup_stack") else None,
            faceup_spread=FaceupCardSpread.__fromdict__(d["faceup_spread"]) if d.get("faceup_spread") else None,
            facedown_stack=PublicFacedownCardStack.__fromdict__(d["facedown_stack"]) if d.get("facedown_stack") else None,
            facedown_spread=PublicFacedownCardSpread.__fromdict__(d["facedown_spread"]) if d.get("facedown_spread") else None,
            discard_faceup_stack=FaceupCardStack.__fromdict__(d["discard_faceup_stack"]) if d.get("discard_faceup_stack") else None,
            discard_facedown_stack=PublicFacedownCardStack.__fromdict__(d["discard_facedown_stack"]) if d.get("discard_facedown_stack") else None,
        )
    
def print_public_deck_stats(deck):
    print("Deck idx:", deck.idx)
    print("Total cards in deck:", len(deck.cards))
    if deck.faceup_stack:
        print("Faceup stack cards:", len(deck.faceup_stack.cards))
    if deck.faceup_spread:
        print("Faceup spread cards:", sum(1 for card in deck.faceup_spread.spots if card is not None))
    if deck.facedown_stack:
        print("Facedown stack cards:", deck.facedown_stack.num_cards)
    if deck.facedown_spread:
        print("Facedown spread cards:", sum(1 for present in deck.facedown_spread.spots if present))
    if deck.discard_faceup_stack:
        print("Discard faceup stack cards:", len(deck.discard_faceup_stack.cards))
    if deck.discard_facedown_stack:
        print("Discard facedown stack cards:", deck.discard_facedown_stack.num_cards)
    

class LegalActionKeep(PClass):
    deck_idx = field(type=int)
    min = field(type=(int, type(None)), initial=None)  # Optional[int]
    max = field(type=(int, type(None)), initial=None)  # Optional[int]
    def get_public(self, state):
        return self
    def to_llm_dict(self):
        return {
            "deck_idx": self.deck_idx,
            "min": self.min,
            "max": self.max,
        }
    def __todict__(self):
        return {
            "deck_idx": self.deck_idx,
            "min": self.min,
            "max": self.max,
        }
    @staticmethod
    def __fromdict__(d):
        return LegalActionKeep(
            deck_idx=d["deck_idx"],
            min=d.get("min"),  # Handle None case
            max=d.get("max"),  # Handle None case
        )
    @staticmethod
    def get_default_action(legal_action, submitted_at):
        actual_min = 0 if legal_action.keep.min is None else legal_action.keep.min
        return Action2(
            submitted_at=submitted_at,
            legal_action=legal_action,
            keep=ActionKeep(
                discard_tray_idxs=pvector(range(actual_min)), 
            )
        )
    

class LegalActionDiscard(PClass):
    deck_idx = field(type=int)
    min = field(type=(int, type(None)), initial=None)  # Optional[int]
    max = field(type=(int, type(None)), initial=None)  # Optional[int]
    def get_public(self, state):
        return self
    def to_llm_dict(self):
        return {
            "deck_idx": self.deck_idx,
            "min": self.min,
            "max": self.max,
        }
    def __todict__(self):
        return {
            "deck_idx": self.deck_idx,
            "min": self.min,
            "max": self.max,
        }
    @staticmethod
    def __fromdict__(d):
        return LegalActionDiscard(
            deck_idx=d["deck_idx"],
            min=d.get("min"),  # Handle None case
            max=d.get("max")  # Handle None case
        )
    @staticmethod
    def get_default_action(legal_action, submitted_at):
        actual_min = 0 if legal_action.discard.min is None else legal_action.discard.min
        return Action2(
            submitted_at=submitted_at,
            legal_action=legal_action,
            discard=ActionDiscard(
                discard_tray_idxs=pvector(range(actual_min)), 
            )
        )


class PublicActionMovePiecesToPathOptional(PClass):
    piece_names = field(type=PVector)  # List[str]
    card_names = field(type=PVector)  # List[int]
    def to_llm_dict(self):
        return {
            "pieces": list(self.piece_names),
            "cards": list(self.card_names),
        }
    def __todict__(self):
        return {
            "piece_names": list(self.piece_names),
            "card_names": list(self.card_names),
        }
    @staticmethod
    def __fromdict__(d):
        return PublicActionMovePiecesToPathOptional(
            piece_names=pvector(d["piece_names"]),
            card_names=pvector(d["card_names"])
        )


class ActionMovePiecesToPathOptional(PClass):
    piece_names = field(type=PVector)  # List[str]
    card_names = field(type=PVector)  # List[str]
    def get_public(self, state):
        return PublicActionMovePiecesToPathOptional(
            piece_names=self.piece_names,
            card_names=self.card_names,
        )
    def to_llm_dict(self):
        return {
            "pieces": list(self.piece_names),
            "cards": list(self.card_names),
        }
    def __todict__(self):
        return {
            "piece_names": list(self.piece_names),
            "card_names": list(self.card_names),
        }
    @staticmethod
    def __fromdict__(d):
        return ActionMovePiecesToPathOptional(
            piece_names=pvector(d["piece_names"]),
            card_names=pvector(d["card_names"])
        )
    

class PublicLegalActionMovePiecesToPath(PClass):
    path = field(type=str)
    def to_llm_dict(self):
        return {
            "path": self.path,
        }
    def __todict__(self):
        return {
            "path": self.path,
        }
    @staticmethod
    def __fromdict__(d):
        return PublicLegalActionMovePiecesToPath(
            path=d["path"]
        )


class LegalActionMovePiecesToPath(PClass):
    path = field(type=str)
    default = field(type=ActionMovePiecesToPathOptional)  # Optional[MovePiecesToPathAction]
    def get_public(self, state):
        return PublicLegalActionMovePiecesToPath(
            path=self.path,
        )
    def to_llm_dict(self):
        return {
            "path": self.path,
            "default": self.default.to_llm_dict(),
        }
    def __todict__(self):
        return {
            "path": self.path,
            "default": self.default.__todict__(),
        }
    @staticmethod
    def __fromdict__(d):
        return LegalActionMovePiecesToPath(
            path=d["path"],
            default=ActionMovePiecesToPathOptional.__fromdict__(d["default"])
        )
    @staticmethod
    def get_default_action(legal_action, submitted_at):
        return Action2(
            submitted_at=submitted_at,
            legal_action=legal_action,
            move_pieces_to_path=legal_action.move_pieces_to_path.default
        )


    
class LegalActionFaceupDraw(PClass):
    deck_idx = field(type=int)
    card_name = field(type=str)
    def get_public(self, state):
        return self
    def to_llm_dict(self):
        return {
            "deck_idx": self.deck_idx,
            "card": self.card_name,
        }
    def __todict__(self):
        return {
            "deck_idx": self.deck_idx,
            "card_name": self.card_name,
        }
    @staticmethod
    def __fromdict__(d):
        return LegalActionFaceupDraw(
            deck_idx=d["deck_idx"],
            card_name=d["card_name"],
        )
    @staticmethod
    def get_default_action(legal_action, submitted_at):
        return Action2(
            submitted_at=submitted_at,
            legal_action=legal_action,
        )



class LegalActionDraw(PClass):
    deck_idx = field(type=int)
    quantity = field(type=int)
    def get_public(self, state):
        return self
    def to_llm_dict(self):
        return {
            "deck_idx": self.deck_idx,
            "quantity": self.quantity,
        }
    def __todict__(self):
        return {
            "deck_idx": self.deck_idx,
            "quantity": self.quantity,
        }
    @staticmethod
    def __fromdict__(d):
        return LegalActionDraw(
            deck_idx=d["deck_idx"],
            quantity=d["quantity"]
        )
    @staticmethod
    def get_default_action(legal_action, submitted_at):
        return Action2(
            submitted_at=submitted_at,
            legal_action=legal_action,
        )


class LegalActionDrawDiscard(PClass):
    deck_idx = field(type=int)
    quantity = field(type=int)
    min = field(type=(int, type(None)), initial=None)  # Optional[int]
    max = field(type=(int, type(None)), initial=None)  # Optional[int]
    def get_public(self, state):
        return self
    def to_llm_dict(self):
        return {
            "deck_idx": self.deck_idx,
            "quantity": self.quantity,
            "min": self.min,
            "max": self.max,
        }
    def __todict__(self):
        return {
            "deck_idx": self.deck_idx,
            "quantity": self.quantity,
            "min": self.min,
            "max": self.max,
        }
    @staticmethod
    def __fromdict__(d):
        return LegalActionDrawDiscard(
            deck_idx=d["deck_idx"],
            quantity=d["quantity"],
            min=d.get("min"),  # Handle None case
            max=d.get("max")  # Handle None case
        )
    @staticmethod
    def get_default_action(legal_action, submitted_at):
        return Action2(
            submitted_at=submitted_at,
            legal_action=legal_action,
        )


class PublicLegalAction(PClass):
    player_idx = field(type=int)
    name = field(type=str)
    discard = field(type=(LegalActionDiscard, type(None)), initial=None)  # LegalActionDiscard
    keep = field(type=(LegalActionKeep, type(None)), initial=None)  # LegalActionKeep
    draw = field(type=(LegalActionDraw, type(None)), initial=None)  # LegalActionDraw
    draw_discard = field(type=(LegalActionDrawDiscard, type(None)), initial=None)  # LegalActionDrawDiscard
    faceup_draw = field(type=(LegalActionFaceupDraw, type(None)), initial=None)  # LegalActionFaceupDraw
    move_pieces_to_path = field(type=(PublicLegalActionMovePiecesToPath, type(None)), initial=None)  # PublicLegalActionMovePiecesToPath
    def to_llm_dict(self):
        return {
            "player_idx": self.player_idx,
            "name": self.name,
            "discard": self.discard.to_llm_dict() if self.discard else None,
            "keep": self.keep.to_llm_dict() if self.keep else None,
            "draw": self.draw.to_llm_dict() if self.draw else None,
            "draw_discard": self.draw_discard.to_llm_dict() if self.draw_discard else None,
            "faceup_draw": self.faceup_draw.to_llm_dict() if self.faceup_draw else None,
            "move_pieces_to_path": self.move_pieces_to_path.to_llm_dict() if self.move_pieces_to_path else None,
        }
    def __todict__(self):
        return {
            "player_idx": self.player_idx,
            "name": self.name,
            "discard": self.discard.__todict__() if self.discard else None,
            "keep": self.keep.__todict__() if self.keep else None,
            "draw": self.draw.__todict__() if self.draw else None,
            "draw_discard": self.draw_discard.__todict__() if self.draw_discard else None,
            "faceup_draw": self.faceup_draw.__todict__() if self.faceup_draw else None,
            "move_pieces_to_path": self.move_pieces_to_path.__todict__() if self.move_pieces_to_path else None,
        }
    @staticmethod
    def __fromdict__(d):
        return PublicLegalAction(
            player_idx=d["player_idx"],
            name=d["name"],
            discard=LegalActionDiscard.__fromdict__(d["discard"]) if d.get("discard") else None,
            keep=LegalActionKeep.__fromdict__(d["keep"]) if d.get("keep") else None,
            draw=LegalActionDraw.__fromdict__(d["draw"]) if d.get("draw") else None,
            draw_discard=LegalActionDrawDiscard.__fromdict__(d["draw_discard"]) if d.get("draw_discard") else None,
            faceup_draw=LegalActionFaceupDraw.__fromdict__(d["faceup_draw"]) if d.get("faceup_draw") else None,
            move_pieces_to_path=LegalActionMovePiecesToPath.__fromdict__(d["move_pieces_to_path"]) if d.get("move_pieces_to_path") else None,
        )


class LegalAction(PClass):
    code = field(type=(str, type(None)), initial=None)  # Optional[str]
    player_idx = field(type=int)
    name = field(type=str)
    title = field(type=(str, type(None)), initial=None)  # Optional[str]
    instruction = field(type=(str, type(None)), initial=None)  # Optional[str]
    allotted_seconds = field(type=int, initial=INITIAL_ALLOTTED_SECONDS)  # int
    allotted_since_action_idx = field(type=int, initial=-1)  # int
    btn_text = field(type=(str, type(None)), initial=None)  # Optional[str]
    discard = field(type=(LegalActionDiscard, type(None)), initial=None)  # LegalActionDiscard
    keep = field(type=(LegalActionKeep, type(None)), initial=None)  # LegalActionKeep
    draw = field(type=(LegalActionDraw, type(None)), initial=None)  # LegalActionDraw
    draw_discard = field(type=(LegalActionDrawDiscard, type(None)), initial=None)  # LegalActionDrawDiscard
    faceup_draw = field(type=(LegalActionFaceupDraw, type(None)), initial=None)  # LegalActionFaceupDraw
    move_pieces_to_path = field(type=(LegalActionMovePiecesToPath, type(None)), initial=None)  # LegalActionMovePiecesToPath
    auto_preferred = field(type=bool, initial=False)  # bool
    def get_default_action(self):
        submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.discard:
            return LegalActionDiscard.get_default_action(self, submitted_at)
        if self.keep:
            return LegalActionKeep.get_default_action(self, submitted_at)
        if self.draw:
            return LegalActionDraw.get_default_action(self, submitted_at)
        if self.draw_discard:
            return LegalActionDrawDiscard.get_default_action(self, submitted_at)
        if self.faceup_draw:
            return LegalActionFaceupDraw.get_default_action(self, submitted_at)
        if self.move_pieces_to_path:
            return LegalActionMovePiecesToPath.get_default_action(self, submitted_at)
        return None
    def get_public(self, state):
        return PublicLegalAction(
            player_idx=self.player_idx,
            name=self.name,
            discard=self.discard.get_public(state) if self.discard else None,
            keep=self.keep.get_public(state) if self.keep else None,
            draw=self.draw.get_public(state) if self.draw else None,
            draw_discard=self.draw_discard.get_public(state) if self.draw_discard else None,
            faceup_draw=self.faceup_draw.get_public(state) if self.faceup_draw else None,
            move_pieces_to_path=self.move_pieces_to_path.get_public(state) if self.move_pieces_to_path else None,
        )
    def __eq__(self, other):
        return self.__todict__() == other.__todict__()
    def to_llm_dict(self):
        d = {
            "code": self.code,
            "name": self.name,
        }
        if self.discard:
            d["discard"] = self.discard.to_llm_dict()
        if self.keep:
            d["keep"] = self.keep.to_llm_dict()
        if self.draw:
            d["draw"] = self.draw.to_llm_dict()
        if self.draw_discard:
            d["draw_discard"] = self.draw_discard.to_llm_dict()
        if self.faceup_draw:
            d["faceup_draw"] = self.faceup_draw.to_llm_dict()
        if self.move_pieces_to_path:
            d["move_pieces_to_path"] = self.move_pieces_to_path.to_llm_dict()
        return d
    def __todict__(self):
        return {
            "code": self.code,
            "player_idx": self.player_idx,
            "name": self.name,
            "title": self.title,
            "instruction": self.instruction,
            "allotted_seconds": self.allotted_seconds,
            "allotted_since_action_idx": self.allotted_since_action_idx,
            "btn_text": self.btn_text,
            "discard": self.discard.__todict__() if self.discard else None,
            "keep": self.keep.__todict__() if self.keep else None,
            "draw": self.draw.__todict__() if self.draw else None,
            "draw_discard": self.draw_discard.__todict__() if self.draw_discard else None,
            "faceup_draw": self.faceup_draw.__todict__() if self.faceup_draw else None,
            "move_pieces_to_path": self.move_pieces_to_path.__todict__() if self.move_pieces_to_path else None,
            "auto_preferred": self.auto_preferred,
        }
    @staticmethod
    def __fromdict__(d):
        return LegalAction(
            code=d.get("code"),  # Handle None case
            player_idx=d["player_idx"],
            name=d["name"],
            title=d.get("title"),  # Handle None case
            instruction=d.get("instruction"),  # Handle None case
            allotted_seconds=d.get("allotted_seconds", DEFAULT_ALLOTTED_SECONDS),  # Handle None case
            allotted_since_action_idx=d.get("allotted_since_action_idx", -1),  # Handle None case
            btn_text=d.get("btn_text"),  # Handle None case
            discard=LegalActionDiscard.__fromdict__(d["discard"]) if d.get("discard") else None,
            keep=LegalActionKeep.__fromdict__(d["keep"]) if d.get("keep") else None,
            draw=LegalActionDraw.__fromdict__(d["draw"]) if d.get("draw") else None,
            draw_discard=LegalActionDrawDiscard.__fromdict__(d["draw_discard"]) if d.get("draw_discard") else None,
            faceup_draw=LegalActionFaceupDraw.__fromdict__(d["faceup_draw"]) if d.get("faceup_draw") else None,
            move_pieces_to_path=LegalActionMovePiecesToPath.__fromdict__(d["move_pieces_to_path"]) if d.get("move_pieces_to_path") else None,
            auto_preferred=d.get("auto_preferred"),  # Handle None case
        )
    

def short_hash(s, length=8):
    return hashlib.sha256(s.encode()).hexdigest()[:length]


def init_legal_action(**kwargs):
    legal_action = LegalAction(**kwargs)
    action_str = json.dumps(legal_action.__todict__(), sort_keys=True)
    return legal_action.set(code=short_hash(action_str))


class PublicActionDiscard(PClass):
    discard_tray_idxs = field(type=PVector)  # List[int]
    def __todict__(self):
        return {
            "discard_tray_idxs": list(self.discard_tray_idxs),
        }
    @staticmethod
    def __fromdict__(d):
        return PublicActionDiscard(
            discard_tray_idxs=pvector(d["discard_tray_idxs"])
        )


class ActionDiscard(PClass):
    discard_tray_idxs = field(type=PVector)  # List[int]
    def get_public(self, state):
        return PublicActionDiscard(
            discard_tray_idxs=self.discard_tray_idxs,
        )
    def __todict__(self):
        return {
            "discard_tray_idxs": list(self.discard_tray_idxs),
        }
    @staticmethod
    def __fromdict__(d):
        return ActionDiscard(
            discard_tray_idxs=pvector(d["discard_tray_idxs"])
        )


class PublicActionKeep(PClass):
    discard_tray_idxs = field(type=PVector)  # List[int]
    def __todict__(self):
        return {
            "discard_tray_idxs": list(self.discard_tray_idxs),
        }
    @staticmethod
    def __fromdict__(d):
        return PublicActionKeep(
            discard_tray_idxs=pvector(d["discard_tray_idxs"])
        )


class ActionKeep(PClass):
    discard_tray_idxs = field(type=PVector)  # List[int]
    def get_public(self, state):
        return PublicActionKeep(
            discard_tray_idxs=self.discard_tray_idxs,
        )
    def __todict__(self):
        return {
            "discard_tray_idxs": list(self.discard_tray_idxs),
        }
    @staticmethod
    def __fromdict__(d):
        return ActionKeep(
            discard_tray_idxs=pvector(d["discard_tray_idxs"])
        )


class PublicAction(PClass):
    submitted_at = field(type=str)
    player_idx = field(type=int)
    name = field(type=str)
    legal_action = field(type=PublicLegalAction)
    discard = field(type=(PublicActionDiscard, type(None)), initial=None)  # PublicActionDiscard
    keep = field(type=(PublicActionKeep, type(None)), initial=None)  # PublicActionKeep
    move_pieces_to_path = field(type=(PublicActionMovePiecesToPathOptional, type(None)), initial=None)  # PublicActionMovePiecesToPathOptional)
    def __todict__(self):
        return {
            "submitted_at": self.submitted_at,
            "player_idx": self.player_idx,
            "name": self.name,
            "legal_action": self.legal_action.__todict__(),
            "discard": self.discard.__todict__() if self.discard else None,
            "keep": self.keep.__todict__() if self.keep else None,
            "move_pieces_to_path": self.move_pieces_to_path.__todict__() if self.move_pieces_to_path else None,
        }
    @staticmethod
    def __fromdict__(d):
        return PublicAction(
            submitted_at=d["submitted_at"],
            player_idx=d["player_idx"],
            name=d["name"],
            legal_action=PublicLegalAction.__fromdict__(d["legal_action"]),
            discard=PublicActionDiscard.__fromdict__(d["discard"]) if d.get("discard") else None,
            keep=PublicActionKeep.__fromdict__(d["keep"]) if d.get("keep") else None,
            move_pieces_to_path=PublicActionMovePiecesToPathOptional.__fromdict__(d["move_pieces_to_path"]) if d.get("move_pieces_to_path") else None,
        )


class Action2(PClass):
    submitted_at = field(type=str)  # str
    legal_action = field(type=LegalAction) 
    discard = field(type=(ActionDiscard, type(None)), initial=None)  # ActionDiscard
    keep = field(type=(ActionKeep, type(None)), initial=None)  # ActionKeep
    move_pieces_to_path = field(type=(ActionMovePiecesToPathOptional, type(None)), initial=None)  # ActionMovePiecesToPath
    def get_public(self, state):
        return PublicAction(
            submitted_at=self.submitted_at,
            player_idx=self.legal_action.player_idx,
            name=self.legal_action.name,
            legal_action=self.legal_action.get_public(state),
            discard=self.discard.get_public(state) if self.discard else None,
            keep=self.keep.get_public(state) if self.keep else None,
            move_pieces_to_path=self.move_pieces_to_path.get_public(state) if self.move_pieces_to_path else None,
        )
    def __todict__(self):
        return {
            "submitted_at": self.submitted_at,
            "legal_action": self.legal_action.__todict__(),
            "discard": self.discard.__todict__() if self.discard else None,
            "keep": self.keep.__todict__() if self.keep else None,
            "move_pieces_to_path": self.move_pieces_to_path.__todict__() if self.move_pieces_to_path else None,
        }
    @staticmethod
    def __fromdict__(d):
        return Action2(
            submitted_at=d["submitted_at"],
            legal_action=LegalAction.__fromdict__(d["legal_action"]),
            discard=ActionDiscard.__fromdict__(d["discard"]) if d.get("discard") else None,
            keep=ActionKeep.__fromdict__(d["keep"]) if d.get("keep") else None,
            move_pieces_to_path=ActionMovePiecesToPathOptional.__fromdict__(d["move_pieces_to_path"]) if d.get("move_pieces_to_path") else None,
        )
    

class DeckStatus(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    faceup_stack = field(type=(FaceupCardStack, type(None)), initial=None)
    faceup_spread = field(type=(FaceupCardSpread, type(None)), initial=None)
    facedown_stack = field(type=(FacedownCardStack, type(None)), initial=None)
    facedown_spread = field(type=(FacedownCardSpread, type(None)), initial=None)
    discard_faceup_stack = field(type=(FaceupCardStack, type(None)), initial=None)
    discard_facedown_stack = field(type=(FacedownCardStack, type(None)), initial=None)
    def to_llm_dict(self):
        return {
            "deck": f"deck-{self.idx}",
            "faceup_stack": self.faceup_stack.__todict__() if self.faceup_stack else None,
            "faceup_spread": self.faceup_spread.__todict__() if self.faceup_spread else None,
            "facedown_stack": self.facedown_stack.__todict__() if self.facedown_stack else None,
            "facedown_spread": self.facedown_spread.__todict__() if self.facedown_spread else None,
            "discard_faceup_stack": self.discard_faceup_stack.__todict__() if self.discard_faceup_stack else None,
            "discard_facedown_stack": self.discard_facedown_stack.__todict__() if self.discard_facedown_stack else None,
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "faceup_stack": self.faceup_stack.__todict__() if self.faceup_stack else None,
            "faceup_spread": self.faceup_spread.__todict__() if self.faceup_spread else None,
            "facedown_stack": self.facedown_stack.__todict__() if self.facedown_stack else None,
            "facedown_spread": self.facedown_spread.__todict__() if self.facedown_spread else None,
            "discard_faceup_stack": self.discard_faceup_stack.__todict__() if self.discard_faceup_stack else None,
            "discard_facedown_stack": self.discard_facedown_stack.__todict__() if self.discard_facedown_stack else None,
        }
    @staticmethod
    def __fromdict__(d):
        return DeckStatus(
            idx=d["idx"],
            uuid=d["uuid"],
            faceup_stack=FaceupCardStack.__fromdict__(d["faceup_stack"]) if d.get("faceup_stack") else None,
            faceup_spread=FaceupCardSpread.__fromdict__(d["faceup_spread"]) if d.get("faceup_spread") else None,
            facedown_stack=FaceupCardStack.__fromdict__(d["facedown_stack"]) if d.get("facedown_stack") else None,
            facedown_spread=FaceupCardSpread.__fromdict__(d["facedown_spread"]) if d.get("facedown_spread") else None,
            discard_faceup_stack=FaceupCardStack.__fromdict__(d["discard_faceup_stack"]) if d.get("discard_faceup_stack") else None,
            discard_facedown_stack=FaceupCardStack.__fromdict__(d["discard_facedown_stack"]) if d.get("discard_facedown_stack") else None,
        )


class Deck(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    cards = field(type=PVector)  # PVector[Card]
    def to_llm_dict(self):
        return {
            "name": f"deck-{self.idx}",
            'cards': [card.to_llm_dict() for card in self.cards],
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            'cards': [card.__todict__() for card in self.cards],
        }
    @staticmethod
    def __fromdict__(d):
        return Deck(
            idx=d["idx"],
            uuid=d["uuid"],
            cards=pvector([Card.__fromdict__(card) for card in d["cards"]]),
        )


class CandidateDeck(PClass):
    deck_idx = field(type=int)
    candidates = field(type=PVector)  # List[str]
    notes = field(type=PVector)  # List[str]
    def __todict__(self):
        return {
            'deck_idx': self.deck_idx,
            'candidates': list(self.candidates),
            'notes': list(self.notes),
        }
    @staticmethod
    def __fromdict__(d):
        return CandidateDeck(
            deck_idx=d["deck_idx"],
            candidates=pvector(d["candidates"]),
            notes=pvector(d["notes"]),
        )    


class PieceTemplate(PClass):
    uuid = field(type=str)
    name = field(type=str)
    def to_llm_dict(self):
        return {
            "name": self.name,
        }
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
        }
    @staticmethod
    def __fromdict__(d):
        return PieceTemplate(
            uuid=d["uuid"],
            name=d["name"]
        )


class Piece(PClass):
    idx = field(type=int)
    name = field(type=str)
    pile_idx = field(type=int)
    player_idx = field(type=int)
    piece_template_idx = field(type=int)
    def to_llm_dict(self):
        return {
            "name": self.name,
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "name": self.name,
            "pile_idx": self.pile_idx,
            "player_idx": self.player_idx,
            "piece_template_idx": self.piece_template_idx,
        }
    @staticmethod
    def __fromdict__(d):
        return Piece(
            idx=d["idx"],
            name=d["name"],
            pile_idx=d["pile_idx"],
            player_idx=d["player_idx"],
            piece_template_idx=d["piece_template_idx"],
        )
    

class Pile(PClass):
    idx = field(type=int)
    player_idx = field(type=(int, type(None)), initial=None)
    num_pieces = field(type=int, initial=0)
    pieces = field(type=PVector)  # List[Piece]
    def to_llm_dict(self):
        return {
            "idx": self.idx,
            "player_idx": self.player_idx,
            "num_pieces": self.num_pieces,
            "pieces": [x.name for x in self.pieces],
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "player_idx": self.player_idx,
            "num_pieces": self.num_pieces,
            "pieces": [piece.__todict__() for piece in self.pieces],
        }
    @staticmethod
    def __fromdict__(d):
        return Pile(
            idx=d["idx"],
            player_idx=d["player_idx"],
            num_pieces=d["num_pieces"],
            pieces=pvector([Piece.__fromdict__(piece) for piece in d["pieces"]]),
        )
    

class Segment(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    name = field(type=str)
    unit_idx = field(type=(int, type(None)), initial=None)  # Optional[int]
    unit_uuid = field(type=(str, type(None)), initial=None)  # Optional[str]
    piece_names = field(type=PVector, initial=v())  # List[str]
    def to_llm_dict(self):
        return {
            "name": self.name,
            "resource": f"resource-{self.unit_idx}" if self.unit_idx is not None else None,
            "pieces": list(self.piece_names),
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "name": self.name,
            "unit_idx": self.unit_idx,
            "unit_uuid": self.unit_uuid,
            "piece_names": list(self.piece_names),
        }
    @staticmethod
    def __fromdict__(d):
        return Segment(
            idx=d["idx"],
            uuid=d["uuid"],
            name=d["name"],
            unit_idx=d["unit_idx"],
            unit_uuid=d["unit_uuid"],
            piece_names=pvector(d["piece_names"]),
        )
    

class SegmentRecord(PClass):
    segment_idx = field(type=int)
    piece_names = field(type=PVector)  # List[str]
    def __todict__(self):
        return {
            "segment_idx": self.segment_idx,
            "piece_names": list(self.piece_names),
        }
    @staticmethod
    def __fromdict__(d):
        return SegmentRecord(
            segment_idx=d["segment_idx"],
            piece_names=pvector(d["piece_names"]),
        )


def init_segment_record(segment: Segment) -> SegmentRecord:
    return SegmentRecord(
        segment_idx=segment.idx,
        piece_names=v(),
    )


class Path(PClass):
    idx = field(type=int)
    name = field(type=str)
    edge_idx = field(type=int)
    edge_uuid = field(type=str)
    segments = field(type=PVector)  # List[Segment]
    score = field(type=int)
    def to_llm_dict(self):
        return {
            "name": self.name,
            "segments": [segment.to_llm_dict() for segment in self.segments],
            "score": self.score,
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "name": self.name,
            "edge_idx": self.edge_idx,
            "edge_uuid": self.edge_uuid,
            "segments": [segment.__todict__() for segment in self.segments],
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return Path(
            idx=d["idx"],
            name=d["name"],
            edge_idx=d["edge_idx"],
            edge_uuid=d["edge_uuid"],
            segments=pvector([Segment.__fromdict__(segment) for segment in d["segments"]]),
            score=d["score"],
        )


class Edge(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    start_point_uuid = field(type=str)
    end_point_uuid = field(type=str)
    node_1_uuid = field(type=str)
    node_2_uuid = field(type=str)
    node_1_idx = field(type=int)
    node_2_idx = field(type=int)
    paths = field(type=PVector)  # List[Path]
    def to_llm_dict(self):
        return {
            "idx": self.idx,
            "name": f"edge-{self.idx}",
            "endpoints": [f"node-{self.node_1_idx}", f"node-{self.node_2_idx}"],
            "paths": [path.to_llm_dict() for path in self.paths],
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "start_point_uuid": self.start_point_uuid,
            "end_point_uuid": self.end_point_uuid,
            "node_1_uuid": self.node_1_uuid,
            "node_2_uuid": self.node_2_uuid,
            "node_1_idx": self.node_1_idx,
            "node_2_idx": self.node_2_idx,
            "paths": [path.__todict__() for path in self.paths],
        }
    @staticmethod
    def __fromdict__(d):
        return Edge(
            idx=d["idx"],
            uuid=d["uuid"],
            start_point_uuid=d["start_point_uuid"],
            end_point_uuid=d["end_point_uuid"],
            node_1_uuid=d["node_1_uuid"],
            node_2_uuid=d["node_2_uuid"],
            node_1_idx=d["node_1_idx"],
            node_2_idx=d["node_2_idx"],
            paths=pvector([Path.__fromdict__(path) for path in d["paths"]]),
        )


class Goal(PClass):
    idx= field(type=int)
    uuid= field(type=str)
    name = field(type=str)
    node_uuids = field(type=PVector)  # List[str]
    node_names = field(type=(PVector, type(None)), initial=None)
    edge_names = field(type=(PVector, type(None)), initial=None)
    region_names = field(type=(PVector, type(None)), initial=None)
    score = field(type=int)
    def to_llm_dict(self):
        d = {
            "name": self.name,
            "score": self.score,
        }
        if self.node_names is not None:
            d["nodes"] = list(self.node_names)
        if self.edge_names is not None:
            d["edges"] = list(self.edge_names)
        if self.region_names is not None:
            d["regions"] = list(self.region_names)
        return d
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "name": self.name,
            "node_uuids": list(self.node_uuids) if self.node_uuids is not None else None,
            "node_names": list(self.node_names) if self.node_names is not None else None,
            "edge_names": list(self.edge_names) if self.edge_names is not None else None,
            "region_names": list(self.region_names) if self.region_names is not None else None,
            "score": self.score,
        }
    @staticmethod
    def __fromdict__(d):
        return Goal(
            idx=d["idx"],
            uuid=d["uuid"],
            name=d["name"],
            node_uuids=pvector(d["node_uuids"]) if d.get("node_uuids") else None,
            node_names=pvector(d["node_names"]) if d.get("node_names") else None,
            edge_names=pvector(d["edge_names"]) if d.get("edge_names") else None,
            region_names=pvector(d["region_names"]) if d.get("region_names") else None,
            score=d["score"],
        )


class Node(PClass):
    idx = field(type=int)
    uuid = field(type=str)
    name = field(type=str)
    pieces = field(type=PVector)  # List[str]
    def to_llm_dict(self):
        return {
            "idx": self.idx,
            "name": f"node-{self.idx}",
        }
    def __todict__(self):
        return {
            "idx": self.idx,
            "uuid": self.uuid,
            "name": self.name,
            "pieces": list(self.pieces)
        }
    @staticmethod
    def __fromdict__(d):
        return Node(
            idx=d["idx"],
            uuid=d["uuid"],
            name=d["name"],
            pieces=pvector(d["pieces"])
        )
    

class Region(PClass):
    uuid = field(type=str)
    node_uuids = field(type=PVector)  # List[str]
    pieces = field(type=PVector)  # List[Piece]
    def __todict__(self):
        return {
            "uuid": self.uuid,
            "node_uuids": list(self.node_uuids),
            "pieces": [piece.__todict__() if hasattr(piece, '__todict__') else piece for piece in self.pieces],
        }
    @staticmethod
    def __fromdict__(d):
        return Region(
            uuid=d["uuid"],
            node_uuids=pvector(d["node_uuids"]),
            pieces=pvector([Piece.__fromdict__(piece) if isinstance(piece, dict) else piece for piece in d["pieces"]]),
        )
    

class LongestTrailBonusPlayerStatus(PClass):
    length = field(type=int)
    def __todict__(self):
        return {
            "length": self.length,
        }
    @staticmethod
    def __fromdict__(d):
        return LongestTrailBonusPlayerStatus(
            length=d["length"]
        )


class BonusPlayerStatus(PClass):
    player_idx = field(type=int)
    score = field(type=int)
    longest_trail = field(type=(LongestTrailBonusPlayerStatus, type(None)), initial=None)  # Optional[LongestTrailBonusPlayerStatus]
    def __todict__(self):
        return {
            "player_idx": self.player_idx,
            "score": self.score,
            "longest_trail": self.longest_trail.__todict__() if self.longest_trail else None,
        }
    @staticmethod
    def __fromdict__(d):
        return BonusPlayerStatus(
            player_idx=d["player_idx"],
            score=d["score"],
            longest_trail=LongestTrailBonusPlayerStatus.__fromdict__(d["longest_trail"]) if d.get("longest_trail") else None,
        )


class BonusStatus(PClass):
    bonus_uuid = field(type=str)
    winners = field(type=PVector)
    player_statuses = field(type=PVector)  # List[BonusPlayerStatus|None]
    def __todict__(self):
        return {
            "bonus_uuid": self.bonus_uuid,
            "winners": list(self.winners),
            "player_statuses": [status.__todict__() for status in self.player_statuses],
        }
    @staticmethod
    def __fromdict__(d):
        return BonusStatus(
            bonus_uuid=d["bonus_uuid"],
            winners=pvector(d["winners"]),
            player_statuses=pvector([BonusPlayerStatus.__fromdict__(status) for status in d.get("player_statuses", [])]),
        )


#==
# uuid2piece
#==#


class State(PClass):
    game_config = field(type=GameConfig)
    rng = field(type=random.Random)
    deck_statuses = field(type=PVector)  # List[DeckStatus]
    piles = field(type=PVector)  # List[Pile]
    players = field(type=PVector)  # List[Player]
    history = field(type=PVector)  # List[Action2]
    last_to_play = field(type=(int, type(None)), initial=None)
    terminal = field(type=bool, initial=False)
    segment_records = field(type=PVector)  # List[SegmentRecord]
    player_idxs = field(type=PVector)  # List[int]
    bonus_statuses = field(type=PVector)  # List[BonusStatus]
    legal_actions = field(type=PVector)  # List[LegalAction]
    winners = field(type=PVector)  # List[int]
    nodes = field(type=PVector, initial=v())  # List[Node]
    edges = field(type=PVector, initial=v())  # List[Edge]
    def __todict__(self):
        return {
            "game_config": self.game_config.__todict__(),
            "rng": rng2json(self.rng),
            "deck_statuses": [deck_status.__todict__() for deck_status in self.deck_statuses],
            "piles": [pile.__todict__() for pile in self.piles],
            "players": [player.__todict__() for player in self.players],
            "history": [action.__todict__() for action in self.history],
            "last_to_play": self.last_to_play,
            "terminal": self.terminal,
            "segment_records": [segment.__todict__() for segment in self.segment_records],
            "player_idxs": list(self.player_idxs),
            "bonus_statuses": [status.__todict__() for status in self.bonus_statuses],
            "legal_actions": [action.__todict__() for action in self.legal_actions],
            "winners": list(self.winners),
            "nodes": [node.__todict__() for node in self.nodes],
            "edges": [edge.__todict__() for edge in self.edges],
        }
    @staticmethod
    def __fromdict__(d):
        return State(
            game_config=GameConfig.__fromdict__(d["game_config"]),
            rng=json2rng(d["rng"]),
            deck_statuses=pvector([DeckStatus.__fromdict__(deck_status) for deck_status in d["deck_statuses"]]),
            piles=pvector([Pile.__fromdict__(pile) for pile in d["piles"]]),
            players=pvector([Player.__fromdict__(player) for player in d["players"]]),
            history=pvector([Action2.__fromdict__(action) for action in d["history"]]),
            last_to_play=d.get("last_to_play"),
            terminal=d.get("terminal"),
            segment_records=pvector([SegmentRecord.__fromdict__(s) for s in d["segment_records"]]),
            player_idxs=pvector(d["player_idxs"]),
            bonus_statuses=pvector([BonusStatus.__fromdict__(x) for x in d["bonus_statuses"]]),
            legal_actions=pvector([LegalAction.__fromdict__(x) for x in d["legal_actions"]]),
            winners=pvector(d["winners"]),
            nodes=pvector([Node.__fromdict__(x) for x in d["nodes"]]),
            edges=pvector([Edge.__fromdict__(x) for x in d["edges"]]),
        )


@dispatch(State)
def getpublicgameconfig(state):
    return getpublicgameconfig(state.game_config)


@dispatch(State, str)
def getpiecefromname(k, name):
    return getpiecefromname(k.game_config, name)


@dispatch(GameConfig, str)
def getpiecefromname(game_config, name):
    # sample_name = "pile-0-piece-12"
    pile_idx = int(name.split("-")[1])
    piece_idx = int(name.split("-")[3])
    return game_config.starting_piles[pile_idx].pieces[piece_idx]


def getcardfromname(k, name):
    # sample_name = "deck-0-card-12"
    deck_idx = int(name.split("-")[1])
    card_idx = int(name.split("-")[3])
    return k.game_config.starting_decks[deck_idx].cards[card_idx]
    

@dispatch(GameConfig)
def init_blank_state_kernel(game_config):
    fig = game_config.fig
    board_config = fig.board_config
    segment_records = pvector(
        [
            init_segment_record(segment) for segment in fig.segments
        ]
    )
    return init_state_kernel(
        game_config,
        segment_records,
    )


@dispatch(GameConfig, PVector)
def init_state_kernel(game_config, segment_records, **kwargs):
    default_players = pvector([
        Player(
            idx=idx, 
            pieces=v(), 
            cards=v(), 
            discard_tray=v(), 
            graph=calc_player_graph3(game_config, segment_records, idx)
        ) 
        for idx in range(game_config.num_players)
    ])

    fresh_deck_statuses = pvector([
        DeckStatus(
            idx=deck.idx,
            uuid=deck.uuid,
            faceup_stack = FaceupCardStack(cards=v()),
            faceup_spread = FaceupCardSpread(spots=v()),
            facedown_stack = FacedownCardStack(cards=pvector([c.name for c in deck.cards])),
            facedown_spread = FacedownCardSpread(spots=v()),
            discard_faceup_stack = FaceupCardStack(cards=v()),
            discard_facedown_stack = FacedownCardStack(cards=v()),
        )
        for deck in game_config.starting_decks
    ])

    return State(
        game_config=game_config,
        rng=getrng(game_config.seed),
        deck_statuses=kwargs.get('deck_statuses', fresh_deck_statuses),
        piles=kwargs.get('piles', game_config.starting_piles),
        players=kwargs.get('players', default_players),
        player_idxs=kwargs.get('player_idxs', pvector(range(game_config.num_players))),
        history=kwargs.get('history', v()),
        segment_records=segment_records,
        terminal=False,
        winners=v(),
        nodes=game_config.fig.nodes,
        edges=game_config.fig.edges,
    )


# Implementing the following Julia function:
# getnumroutecards(f::Fig) = length(f.board_config.routes)
@dispatch(Fig)
def getnumroutecards(f):
    return len(f.board_config.routes) if f and f.board_config else 0


# Implementing the following Julia function:
# [x.quantity for x in f.board_config.deck_units] |> sum
@dispatch(Fig)
def gettotaldeckcards(f):
    return sum(x.quantity for x in f.board_config.deck_units) if f and f.board_config else 0
    

# Implementing the following Julia function:
# function shuffledeck(deck_size::Int, seed::Int)
#     shuffledeck(collect(1:deck_size), seed)
# end
@dispatch(int, object)
def shuffledeck(deck_size, rng):
    deck = pvector(range(1, deck_size + 1))
    return shuffle_pvector(deck, rng)


@dispatch(PVector, object)
def shuffle_pvector(a, rng):
    return pvector(
        shuffle_list(list(a), rng)
    )


@dispatch(list, object)
def shuffle_list(a, rng):
    rng.shuffle(a)
    return a


class QValueLearningPolicy(PClass):
    qvalue_fn = field()
    epsilon = field(type=float, initial=0.1)  # Epsilon for exploration


class RandoPolicy(PClass):
    pass


# Functions  


# Implementing the following GraphQL type:
# type PlayerScore {
# 	breakdown: [ScoreItem]!
# 	total: Int!
# }
class PlayerScore(PClass):
    breakdown = field(type=PVector)  # List[ScoreItem]
    total = field(type=int)
    def __todict__(self):
        return {
            "breakdown": [x.__todict__() for x in self.breakdown], 
            "total": self.total,
        }
    @staticmethod
    def __fromdict__(d):
        return PlayerScore(
            breakdown=pvector([ScoreItem.__fromdict__(x) for x in d["breakdown"]]),
            total=d["total"]
        )


class PublicPlayerScore(PClass):
    items = field(type=PVector)  # List[ScoreItem]
    total = field(type=int)
    def __todict__(self):
        return {
            "items": [x.__todict__() for x in self.items], 
            "total": self.total,
        }
    @staticmethod
    def __fromdict__(d):
        return PublicPlayerScore(
            items=pvector([ScoreItem.__fromdict__(x) for x in d["items"]]),
            total=d["total"]
        )


class ScoreItemBonus(PClass):
    bonus_uuid = field(type=str)
    def __todict__(self):
        return {
            "bonus_uuid": self.bonus_uuid,
        }
    @staticmethod
    def __fromdict__(d):
        return ScoreItemBonus(
            bonus_uuid=d["bonus_uuid"],
        )


class ScoreItemGoal(PClass):
    goal_idx = field(type=int)
    goal_uuid = field(type=str)
    complete = field(type=bool)
    def to_llm_dict(self):
        return {
            "goal": f"goal-{self.goal_idx}",
            "complete": self.complete,
        }
    def __todict__(self):
        return {
            "goal_idx": self.goal_idx,
            "goal_uuid": self.goal_uuid,
            "complete": self.complete,
        }
    @staticmethod
    def __fromdict__(d):
        return ScoreItemGoal(
            goal_idx=d["goal_idx"],
            goal_uuid=d["goal_uuid"],
            complete=d["complete"],
        )
    

class ScoreItemOwnsPath(PClass):
    path_idx = field(type=int)
    edge_uuid = field(type=str)
    length = field(type=int)
    def __todict__(self):
        return {
            "path_idx": self.path_idx,
            "edge_uuid": self.edge_uuid,
            "length": self.length,
        }
    @staticmethod
    def __fromdict__(d):
        return ScoreItemOwnsPath(
            path_idx=d["path_idx"],
            edge_uuid=d["edge_uuid"],
            length=d["length"],
        )


class ScoreItem(PClass):
    amount = field(type=int)
    description = field(type=(str, type(None)), initial=None)
    owns_path = field(type=(ScoreItemOwnsPath, type(None)), initial=None)  # Optional[ScoreItemOwnsPath]
    goal = field(type=(ScoreItemGoal, type(None)), initial=None)  # Optional[FrozenGoal]
    bonus = field(type=(ScoreItemBonus, type(None)), initial=None)  # Optional[FrozenGoal] 
    def to_llm_dict(self):
        return {
            "amount": self.amount,
            "owns_path": self.owns_path.to_llm_dict() if self.owns_path else None,
            "goal_completion": self.goal.to_llm_dict() if self.goal else None,
            "bonus": self.bonus.to_llm_dict() if self.bonus else None,
        }
    def __todict__(self):
        return {
            "amount": self.amount,
            "description": self.description,
            "owns_path": self.owns_path.__todict__() if self.owns_path else None,
            "goal": self.goal.__todict__() if self.goal else None,
            "bonus": self.bonus.__todict__() if self.bonus else None,
        }
    @staticmethod
    def __fromdict__(d):
        return ScoreItem(
            amount=d["amount"],
            description=d.get("description"),  # Handle None case
            owns_path=ScoreItemOwnsPath.__fromdict__(d["owns_path"]) if d.get("owns_path") else None,
            goal=ScoreItemGoal.__fromdict__(d["goal"]) if d.get("goal") else None,
            bonus=ScoreItemBonus.__fromdict__(d["bonus"]) if d.get("bonus") else None,
        )


class AllottedTime(PClass):
    seconds = field(type=int)
    since_action_idx = field(type=int)
    def __todict__(self):
        return {
            "seconds": self.seconds,
            "since_action_idx": self.since_action_idx,
        }
    @staticmethod
    def __fromdict__(d):
        return AllottedTime(
            seconds=d["seconds"],
            since_action_idx=d["since_action_idx"],
        )


class RemainingAllottedTime(PClass):
    seconds = field(type=int)
    remaining_seconds = field(type=int)
    since_action_idx = field(type=int)
    def __todict__(self):
        return {
            "seconds": self.seconds,
            "remaining_seconds": self.remaining_seconds,
            "since_action_idx": self.since_action_idx,
        }
    @staticmethod
    def __fromdict__(d):
        return RemainingAllottedTime(
            seconds=d["seconds"],
            remaining_seconds=d["remaining_seconds"],
            since_action_idx=d["since_action_idx"],
        )


class PublicState(PClass):
    segment_records = field(type=PVector)  # List[SegmentRecord]
    deadlines = field(type=PVector)  # List[RemainingAllottedTime|None]
    game_started_at = field(type=str)
    allotted_times = field(type=PVector)
    to_play = field(type=PVector)  # List[int]
    bonus_statuses = field(type=PVector)  # List[BonusStatus]
    history = field(type=PVector)  # List[PublicAction]
    player_scores = field(type=PVector)  # List[PublicPlayerScore]
    deck_statuses = field(type=PVector)  # List[PublicDeckStatus]
    piles = field(type=PVector)  # List[Pile]
    player_idxs = field(type=PVector)  # List[int]
    players = field(type=PVector)  # List[PublicPlayer]
    last_to_play = field(type=(int, type(None)), initial=None)
    winners = field(type=PVector)
    terminal = field(type=bool)
    nodes = field(type=PVector)  # PVector[Node]
    edges = field(type=PVector)  # PVector[Edge]
    def to_llm_dict(self):
        return {
            "player_action_order": list(self.player_idxs),
            "deck_statuses": [x.to_llm_dict() for x in self.deck_statuses],
            "players": [x.to_llm_dict() for x in self.players],
            "nodes": [node.to_llm_dict() for node in self.nodes],
            "edges": [edge.to_llm_dict() for edge in self.edges],
        }
    def __todict__(self):
        return {
            "segment_records": [segment.__todict__() for segment in self.segment_records],
            "deadlines": [deadline.__todict__() if deadline else None for deadline in self.deadlines],
            "game_started_at": self.game_started_at,
            "allotted_times": [allotted_time.__todict__() if allotted_time else None for allotted_time in self.allotted_times], # List[AllottedTime|None]
            "to_play": list(self.to_play),
            "bonus_statuses": [bs.__todict__() for bs in self.bonus_statuses],
            "history": [x.__todict__() for x in self.history],
            "player_scores": [x.__todict__() for x in self.player_scores],
            "deck_statuses": [deck_status.__todict__() for deck_status in self.deck_statuses],
            "piles": [pile.__todict__() for pile in self.piles],
            "player_idxs": list(self.player_idxs),
            "players": [x.__todict__() for x in self.players],
            "last_to_play": self.last_to_play,
            "winners": list(self.winners),
            "terminal": self.terminal,
            "nodes": [node.__todict__() for node in self.nodes],
            "edges": [edge.__todict__() for edge in self.edges],
        }
    @staticmethod
    def __fromdict__(d):
        return PublicState(
            segment_records=pvector([SegmentRecord.__fromdict__(x) for x in d["segment_records"]]),
            deadlines=pvector([RemainingAllottedTime.__fromdict__(x) for x in d["deadlines"]]),
            game_started_at=d["game_started_at"],
            allotted_times=pvector([AllottedTime.__fromdict__(x) if x else None for x in d["allotted_times"]]), # List[AllottedTime|None]
            to_play=pvector(d["to_play"]),
            bonus_statuses=pvector([BonusStatus.__fromdict__(x) for x in d["bonus_statuses"]]),
            history=pvector([PublicAction.__fromdict__(x) for x in d["history"]]),
            player_scores=pvector([PublicPlayerScore.__fromdict__(x) for x in d["player_scores"]]),
            regions=pvector([Region.__fromdict__(r) for r in d["regions"]]),
            deck_statuses=pvector([PublicDeckStatus.__fromdict__(deck_status) for deck_status in d["deck_statuses"]]),
            piles=pvector([Pile.__fromdict__(x) for x in d["piles"]]),
            player_idxs=pvector(d["player_idxs"]),
            players=pvector([PublicPlayer.__fromdict__(x) for x in d["players"]]),
            last_to_play=d.get("last_to_play"),
            winners=pvector(d["winners"]),
            terminal=d["terminal"],
            nodes=pvector([Node.__fromdict__(n) for n in d["nodes"]]),
            edges=pvector([Edge.__fromdict__(x) for x in d["edges"]]),
        )


class PlayerState(PClass):
    game_config = field(type=PublicGameConfig)
    public = field(type=PublicState)
    private = field(type=PrivateState)
    def __todict__(self):
        return {
            "game_config": self.game_config.__todict__(),
            "public": self.public.__todict__(),
            "private": self.private.__todict__()
        }
    @staticmethod
    def __fromdict__(d):
        return PlayerState(
            game_config=PublicGameConfig.__fromdict__(d["game_config"]),
            public=PublicState.__fromdict__(d["public"]),
            private=PrivateState.__fromdict__(d["private"])
        )


def autoplay(seed, fig, num_players, policy, log=False):
    game_config = initgameconfig(str(uuid4()), "2025-01-01 00:00:00", fig, num_players, seed)
    s = getinitialstate(game_config)
    actions = v()
    try:

        while not s.terminal:
            if log:
                printstate(s)
            a = getnextaction(s, policy)
            s = getnextstate2(s, a)
            actions = actions.append(a)
        
        if (log):
            printstate(s)
        
    except Exception as e:
        logging.error(f"Something went wrong: {str(e)}", exc_info=True)
    finally:
        return (game_config, actions, s)


def get_regions(board_config):
    return v() # TODO: None for now (need to modify BoardConfig to include regions)


def get_nodes(board_config):
    if board_config and board_config.points:
        return pvector([
            Node(idx=idx, uuid=node.uuid, name=f"{idx}", pieces=v())
            for idx, node in enumerate(board_config.points)
        ])
    return v()


def get_segments(edges):
    segments = []
    for edge in edges:
        for path in edge.paths:
            for segment in path.segments:
                segments.append(segment)
    return pvector(segments)


def get_edges(board_config, nodeuuid2idx, resourceuuid2idx):
    edges = v()
    segment_counter = 0


    for link_idx, link in enumerate(board_config.links):
        node_1_idx=nodeuuid2idx[link.c1]
        node_2_idx=nodeuuid2idx[link.c2]
        matching_board_paths = [p for p in board_config.board_paths if p.link_num == link.num]

        paths = v()
        for board_path_idx, matching_board_path in enumerate(matching_board_paths):
            path_idx = matching_board_path.num - 1

            segments = v()
            for path_segment_idx, s in enumerate(matching_board_path.path.segments):
                segments = segments.append(
                    Segment(
                        idx=segment_counter,
                        name=f"edge-{link_idx}-path-{board_path_idx}-segment-{path_segment_idx}",
                        uuid=s.uuid, 
                        unit_idx=resourceuuid2idx.get(s.unit_uuid) if s.unit_uuid else None,
                        unit_uuid=s.unit_uuid,
                    )
                )
                segment_counter += 1

            path = Path(
                idx=path_idx,
                name=f"edge-{link_idx}-path-{board_path_idx}",
                edge_idx=link_idx,
                edge_uuid=link.uuid,
                segments=segments,
                score=link.score,
            )
            paths = paths.append(path)
        
        if len(paths) == 0:
            print(f"len(board_config.board_paths) = {len(board_config.board_paths)}")
            print("len(board_config.links) =", len(board_config.links))
            raise ValueError(f"No paths found for link {link.uuid} with nodes {link.c1} and {link.c2} and link number {link.num}")

        edges = edges.append(
            Edge(
                uuid=link.uuid,
                idx=link_idx,
                start_point_uuid=link.c1,
                end_point_uuid=link.c2,
                node_1_uuid=link.c1,
                node_2_uuid=link.c2,
                node_1_idx=node_1_idx,
                node_2_idx=node_2_idx,
                paths=paths,
            )
        )

    return edges


def generate_pieces(piece_template, pile_idx, player_idx):
    return pvector([
        Piece(
            idx=idx,
            name=f"pile-{pile_idx}-piece-{idx}",
            piece_template_idx=piece_template.idx,
            pile_idx=pile_idx,
            player_idx=player_idx
        ) for idx in range(piece_template.quantity)
    ])


def generate_cards(dek, resourceuuid2idx, goaluuid2idx):
    cards = v()
    idx = 0
    for dek_card in dek.dek_cards:
        for _ in range(dek_card.quantity):
            card = Card(
                idx=idx,
                deck_idx=dek.idx,
                name=f"deck-{dek.idx}-card-{idx}",
                is_wild=dek_card.is_wild,
                resource_idx=resourceuuid2idx.get(dek_card.resource_uuid) if dek_card.resource_uuid else None,
                resource_uuid=dek_card.resource_uuid,
                goal_uuid=dek_card.goal_uuid,
                goal_idx=goaluuid2idx.get(dek_card.goal_uuid) if dek_card.goal_uuid else None,
            )
            cards = cards.append(card)
            idx += 1

    return cards


@dispatch(Fig, str)
def getsettingvalue(f, setting_name):
    for setting in f.board_config.settings:
        if setting.name == setting_name:
            return json.loads(setting.value_json)
    return None


@dispatch(State, str)
def getsettingvalue(s, setting_name):
    return getsettingvalue(s.game_config.fig, setting_name)


@dispatch(GameConfig)
def getinitialstate(game_config):
    kernel = init_blank_state_kernel(game_config)
    kernel = run_kernel_hooks(kernel, INITIALIZATION_HOOKS, True)
    return init_memoized_state(kernel)


@dispatch(State)
def init_memoized_state(kernel):
    kernel = kernel.set(bonus_statuses=calc_bonus_statuses(kernel))
    kernel = kernel.set(legal_actions=calc_legal_actions3(kernel))
    kernel = handle_player_scores(kernel)
    kernel = handle_last_to_play(kernel)
    kernel = handle_calc_winners(kernel)
    return kernel


def handle_player_scores(kernel):
    return kernel.set(
        players=pvector([
            player.set(score=calc_player_score(kernel, player.idx)) 
            for player in kernel.players
        ])
    )


@dispatch(State)
def calc_bonus_statuses(kernel):
    bonus_statuses = [
        calc_bonus_status3(kernel, bonus)
        for bonus in kernel.game_config.fig.board_config.bonuses
    ]
    bonus_statuses = [bs for bs in bonus_statuses if bs is not None]
    return pvector(bonus_statuses)


@dispatch(State, int)
def calc_player_score(k, player_idx):
    return PlayerScore2(
        public_items=score_public_items(k, player_idx),
        private_items=score_private_items(k, player_idx),
    )


def run_state_hooks(state, hooks, log=False):
    return reduce(
        lambda s, h: run_state_hook(s, h, log), 
        hooks, 
        state
    )


@dispatch(State, list, bool)
def run_kernel_hooks(kernel, hooks, log=False):
    return reduce(
        lambda k, h: run_kernel_hook(k, h, log), 
        hooks, 
        kernel
    )


def run_accept_action_hooks(state, action, hooks, log=False):
    # Just like "run_state_action_hooks", but returns immediately returns True if any hook returns True, otherwise returns False
    for hook in hooks:
        is_accepted, reason = run_state_action_hook(state, action, hook, log)
        if is_accepted is not None and is_accepted:
            return True, reason
        elif is_accepted is not None and not is_accepted:
            return False, reason
    return False, "No hook accepted the action"


def run_state_action_hooks(state, action, hooks, log=False):
    return reduce(
        lambda s, h: run_state_action_hook(s, action, h, log), 
        hooks, 
        state
    )


@dispatch(State, int)
def score_public_items(k, player_idx):
    items = v()
    for edge in k.game_config.fig.edges:
        for path in edge.paths:
            segment_idxs = [s.idx for s in path.segments]
            if len(segment_idxs) > 0:
                first_segment_record = k.segment_records[segment_idxs[0]]
                if len(first_segment_record.piece_names) > 0:
                    piece_name = first_segment_record.piece_names[0]
                    first_piece = getpiecefromname(k, piece_name)
                    if first_piece.player_idx == player_idx:
                        items = items.append(
                            ScoreItem(
                                amount=path.score,
                                owns_path=ScoreItemOwnsPath(
                                    path_idx=path.idx,
                                    edge_uuid=edge.uuid,
                                    length=len(segment_idxs),
                                ),
                                description="Player {} owns edge {}".format(player_idx, edge.uuid),
                            )
                        )
    for bonus_status in k.bonus_statuses:
        bonus_idx = k.game_config.fig.bonusuuid2bonusidx[bonus_status.bonus_uuid]
        bonus = k.game_config.fig.board_config.bonuses[bonus_idx] if bonus_idx is not None else None
        if bonus:
            if player_idx in bonus_status.winners:
                items = items.append(
                    ScoreItem(
                        amount=bonus.score,
                        description="Player {} wins bonus {}".format(player_idx, bonus.code),
                        bonus=ScoreItemBonus(bonus_uuid=bonus.uuid),
                    )
                )
    return items


@dispatch(State, int)
def score_private_items(kernel, player_idx):
    fig = kernel.game_config.fig
    items = v()
    goal_completions = get_goal_completions(kernel, player_idx)
    complete_goal_uuids = [gc.goal_uuid for gc in goal_completions if gc.complete]
    incomplete_goal_uuids = [gc.goal_uuid for gc in goal_completions if not gc.complete]
    for complete_goal_uuid in complete_goal_uuids:
        goal = fig.goals[fig.goaluuid2idx[complete_goal_uuid]]
        items = items.append(
            ScoreItem(
                amount=goal.score,
                description="Player {} completed goal {}".format(player_idx, complete_goal_uuid),
                goal=ScoreItemGoal(goal_idx=goal.idx, goal_uuid=complete_goal_uuid, complete=True)
            )
        )
    for incomplete_goal_uuid in incomplete_goal_uuids:
        goal = fig.goals[fig.goaluuid2idx[incomplete_goal_uuid]]
        items = items.append(
            ScoreItem(
                amount=(-1*goal.score),
                description="Player {} incomplete goal {}".format(player_idx, incomplete_goal_uuid),
                goal=ScoreItemGoal(goal_idx=goal.idx, goal_uuid=incomplete_goal_uuid, complete=False)
            )
        )
    return items


@dispatch(State)
def handle_last_to_play(k):
    if k.last_to_play is None:
        # If any player can less than 3 pieces, the game is terminal
        for player in k.players:
            if len(player.pieces) < 3:
                return k.set(last_to_play=player.idx)
    else:
        if k.last_to_play == k.history[-1].legal_action.player_idx:
            if not k.legal_actions:
                return k.set(terminal=True)
    return k


@dispatch(State)
def getfinalscores3(k):
    return [
        getpublicplayerscore(k, k.players[player_idx].score).total
        for player_idx in range(len(k.players))
    ]


@dispatch(State)
def handle_calc_winners(k):
    if k.terminal:
        players_with_highest_score = v()
        highest_score = -1000
        final_scores = getfinalscores3(k)
        for player_idx in range(len(k.players)):
            final_score = final_scores[player_idx]
            if final_score > highest_score:
                highest_score = final_score
                players_with_highest_score = pvector([player_idx])
            elif final_score == highest_score:
                players_with_highest_score = players_with_highest_score.append(player_idx)
        return k.set(
            winners=players_with_highest_score,
        )

    return k


def calc_bonus_status(game, bonus):
    if not bonus:
        return None
    if bonus.code == "longest-trail":
        return get_bonus_status_longest_trail(game, bonus)
    return None


@dispatch(State, FrozenBonus)
def calc_bonus_status3(kernel, bonus):
    if not bonus:
        return None
    if bonus.code == "longest-trail":
        return get_bonus_status_longest_trail3(kernel, bonus)
    return None


@dispatch(State, FrozenBonus)
def get_bonus_status_longest_trail3(kernel, bonus):
    longest_trail = 0
    winners = v()
    player_longest_trail_lens = v()

    for player_idx in range(kernel.game_config.num_players):
        trail_length = get_longest_path_length3(kernel, player_idx)
        player_longest_trail_lens = player_longest_trail_lens.append(trail_length)
        if trail_length > longest_trail:
            longest_trail = trail_length
            winners = pvector([player_idx])
        elif trail_length == longest_trail and trail_length > 0:
            winners = winners.append(player_idx)

    player_statuses = [
        BonusPlayerStatus(
            player_idx=player_idx,
            score=bonus.score if player_idx in winners else 0,
            longest_trail=LongestTrailBonusPlayerStatus(
                length=player_longest_trail_len
            ),
        )
        for player_idx, player_longest_trail_len in enumerate(player_longest_trail_lens)
    ]

    return BonusStatus(
        bonus_uuid=bonus.uuid,
        winners=winners,
        player_statuses=pvector(player_statuses),
    )


def get_bonus_status_longest_trail(state, bonus):
    longest_trail = 0
    winners = v()
    player_longest_trail_lens = v()

    for player_idx in range(state.game_config.num_players):
        trail_length = get_longest_path_length3(state, player_idx)
        player_longest_trail_lens = player_longest_trail_lens.append(trail_length)
        if trail_length > longest_trail:
            longest_trail = trail_length
            winners = pvector([player_idx])
        elif trail_length == longest_trail and trail_length > 0:
            winners = winners.append(player_idx)

    player_statuses = [
        BonusPlayerStatus(
            player_idx=player_idx,
            score=bonus.score if player_idx in winners else 0,
            longest_trail=LongestTrailBonusPlayerStatus(
                length=player_longest_trail_len
            ),
        )
        for player_idx, player_longest_trail_len in enumerate(player_longest_trail_lens)
    ]

    return BonusStatus(
        bonus_uuid=bonus.uuid,
        winners=winners,
        player_statuses=pvector(player_statuses),
    )


@dispatch(State)
def handle_bonus_statuses(state):
    bonus_statuses = [
        calc_bonus_status(state, bonus)
        for bonus in state.game_config.fig.board_config.bonuses
    ]
    # Remove all None bonus statuses
    bonus_statuses = [bs for bs in bonus_statuses if bs is not None]
    return state.set(bonus_statuses=bonus_statuses)


@dispatch(State, Action2)
def default_handle_action(kernel, action):
    if action.legal_action.discard:
        return handle_discard_action(kernel, action)
    if action.legal_action.keep:
        return handle_keep_action(kernel, action)
    if action.legal_action.move_pieces_to_path:
        kernel = handle_move_pieces_to_path_action(kernel, action)
        return handle_after_move_pieces_to_path_action(kernel, action)
    if action.legal_action.faceup_draw:
        return handle_faceup_draw_action(kernel, action)
    if action.legal_action.draw:
        return handle_draw_action(kernel, action)
    if action.legal_action.draw_discard:
        return handle_draw_discard_action(kernel, action)

    return kernel


@dispatch(State, Action2)
def default_after_accept_action(kernel, action):
    # Remove all actions for matching player of action
    if not kernel or not action or not action.legal_action:
        return kernel
    player_idx = action.legal_action.player_idx
    if player_idx < 0 or player_idx >= len(kernel.players):
        return kernel
    history = kernel.history + [action]
    return kernel.set(
        history=history,
    )


@dispatch(State)
def recycle_decks_if_needed(kernel):
    for deck_idx in range(len(kernel.deck_statuses)):
        # print("recycle_decks_if_needed for deck_idx =", deck_idx)
        kernel = recycle_if_needed(kernel, deck_idx)
    return kernel


@dispatch(State)
def replenish_decks_if_needed(kernel):
    for deck_idx in range(len(kernel.deck_statuses)):
        kernel = replenish_faceup_if_needed(kernel, deck_idx)
    return kernel


@dispatch(State, int, int)
def replenish_faceup_spot_if_needed(kernel, deck_idx, spot_idx):
    deck = kernel.deck_statuses[deck_idx]

    if deck.faceup_spread.spots[spot_idx] is not None:
        return kernel

    if len(deck.facedown_stack.cards) == 0:
        return kernel

    # Pop from facedown stack
    drawn_card = deck.facedown_stack.cards[-1]
    facedown_cards = deck.facedown_stack.cards[:-1]

    # Set in faceup spread
    faceup_spots = deck.faceup_spread.spots.set(spot_idx, drawn_card)

    # Update deck
    deck = deck.set(
        facedown_stack=deck.facedown_stack.set(cards=facedown_cards),
        faceup_spread=deck.faceup_spread.set(spots=faceup_spots)
    )

    # Update kernel
    decks = kernel.deck_statuses.set(deck_idx, deck)
    kernel = kernel.set(deck_statuses=decks)

    kernel = ensure_faceup_spots_valid(kernel)

    return kernel


@dispatch(State, int)
def replenish_faceup_if_needed(kernel, deck_idx):
    deck = kernel.deck_statuses[deck_idx]
    for spot_idx in range(len(deck.faceup_spread.spots)):
        kernel = replenish_faceup_spot_if_needed(kernel, deck_idx, spot_idx)
    return kernel


@dispatch(State, int)
def recycle_if_needed(kernel, deck_idx):
    deck = kernel.deck_statuses[deck_idx]
    if len(deck.facedown_stack.cards) == 0:
        shuffled_discards = list(deck.discard_faceup_stack.cards) + list(deck.discard_facedown_stack.cards)
        kernel.rng.shuffle(shuffled_discards)
        deck = deck.set(
            facedown_stack=FacedownCardStack(cards=pvector(shuffled_discards)),
            discard_faceup_stack=FaceupCardStack(cards=v()),
            discard_facedown_stack=FacedownCardStack(cards=v()),
        )
        kernel = set_deck(kernel, deck.idx, deck)
    return kernel


@dispatch(State, Action2)
def handle_draw_action(kernel, action):
    if not kernel or not action or not action.legal_action or not action.legal_action.draw:
        return kernel
    legal_action = action.legal_action
    draw = legal_action.draw
    player = kernel.players[legal_action.player_idx]
    deck = kernel.deck_statuses[draw.deck_idx]

    if len(deck.facedown_stack.cards) == 0:
        return kernel  # No cards to draw

    for _ in range(draw.quantity):
        # Pop from deck
        drawn_card = deck.facedown_stack.cards[-1]
        facedown_cards = deck.facedown_stack.cards[:-1]

        # Append to player cards
        player_cards = player.cards.append(drawn_card)

        # Update deck and player
        deck = deck.set(facedown_stack=deck.facedown_stack.set(cards=facedown_cards))
        player = player.set(cards=player_cards)

        # Update kernel
        decks = kernel.deck_statuses.set(draw.deck_idx, deck)
        players = kernel.players.set(legal_action.player_idx, player)
        kernel = kernel.set(deck_statuses=decks, players=players)

        kernel = recycle_if_needed(kernel, draw.deck_idx)

        # Refresh references after recycle
        deck = kernel.deck_statuses[draw.deck_idx]
        player = kernel.players[legal_action.player_idx]

    # TODO: extract this out to user-defined function/hook
    # if draw.quantity == 1:
    #     game = append_follow_up_draw_legal_actions(game, action)

    return kernel


@dispatch(State, Action2)
def handle_draw_discard_action(kernel, action):
    if not kernel or not action or not action.legal_action or not action.legal_action.draw_discard:
        return kernel
    legal_action = action.legal_action
    draw_discard = legal_action.draw_discard

    p_idx = legal_action.player_idx
    player = kernel.players[p_idx]
    deck = kernel.deck_statuses[draw_discard.deck_idx]

    if len(deck.facedown_stack.cards) == 0:
        return kernel  # No cards to draw

    for _ in range(draw_discard.quantity):
        # Pop from deck
        drawn_card = deck.facedown_stack.cards[-1]
        facedown_cards = deck.facedown_stack.cards[:-1]

        # Update deck and player
        deck = deck.set(facedown_stack=deck.facedown_stack.set(cards=facedown_cards))
        player = player.set(discard_tray=player.discard_tray.append(drawn_card))

    # Update kernel
    decks = kernel.deck_statuses.set(draw_discard.deck_idx, deck)
    players = kernel.players.set(p_idx, player)
    return kernel.set(
        players=players,
        deck_statuses=decks,
    )


@dispatch(State, Action2)
def get_follow_up_draw_legal_actions(kernel, action):
    to_return = v()
    legal_action = action.legal_action
    if len(kernel.history) >= 2:
        last_action = kernel.history[-2]
        if (last_action.legal_action.player_idx != legal_action.player_idx) or last_action.legal_action.name == "INITIAL-KEEP-GOAL-CARDS":

            if len(kernel.deck_statuses[0].facedown_stack.cards) >= 1:
                to_return = to_return.append(
                    init_legal_action(
                        auto_preferred=True,
                        player_idx=legal_action.player_idx,
                        name="BLIND-DRAW-RESOURCE-CARD",
                        instruction="draw a unit",
                        allotted_seconds=DEFAULT_ALLOTTED_SECONDS,
                        allotted_since_action_idx=(len(kernel.history) - 1),
                        draw=LegalActionDraw(
                            deck_idx=0,
                            quantity=1,
                        )
                    )
                )

            for card_name in kernel.deck_statuses[0].faceup_spread.spots:
                if card_name:
                    if not getcardfromname(kernel, card_name).is_wild:
                        to_return = to_return.append(
                            init_legal_action(
                                player_idx=legal_action.player_idx,
                                name="FACEUP-DRAW-RESOURCE-CARD",
                                instruction="draw a faceup unit",
                                allotted_seconds=DEFAULT_ALLOTTED_SECONDS,
                                allotted_since_action_idx=(len(kernel.history) - 1),
                                faceup_draw=LegalActionFaceupDraw(
                                    deck_idx=0,
                                    card_name=card_name,
                                )
                            )
                        )
    
    return to_return


@dispatch(State, int)
def get_num_faceup_wilds(kernel, deck_idx):
    deck = kernel.deck_statuses[deck_idx]
    non_empty_spots = [spot for spot in deck.faceup_spread.spots if spot]
    if not non_empty_spots:
        return 0
    return sum(1 for card_name in non_empty_spots if getcardfromname(kernel, card_name).is_wild)


@dispatch(State)
def ensure_faceup_spots_valid(kernel):
    for deck in kernel.deck_statuses:
        max_iters = 5
        i = 0
        while i < max_iters and get_num_faceup_wilds(kernel, deck.idx) >= 3:
            kernel = discardfaceup_shuffle_flip(kernel, deck.idx)
            i += 1
    return kernel


@dispatch(State, int)
def discardfaceup_shuffle_flip(kernel, deck_idx):
    deck = kernel.deck_statuses[deck_idx]
    num_faceup_spots = len(deck.faceup_spread.spots)
    discard_faceup_cards = deck.discard_faceup_stack.cards
    for faceup_spot in deck.faceup_spread.spots:
        if faceup_spot:
            discard_faceup_cards = discard_faceup_cards.append(faceup_spot)
    discard_faceup_stack = deck.discard_faceup_stack.set(cards=discard_faceup_cards)
    deck = deck.set(faceup_spread=FaceupCardSpread(spots=v()), discard_faceup_stack=discard_faceup_stack)

    facedown_cards = deck.facedown_stack.cards
    discard_faceup_cards = deck.discard_faceup_stack.cards
    while len(discard_faceup_cards) > 0:
        card = discard_faceup_cards[-1]
        discard_faceup_cards = discard_faceup_cards[:-1]
        facedown_cards = facedown_cards.append(card)
    discard_faceup_stack = deck.discard_faceup_stack.set(cards=discard_faceup_cards)
    facedown_stack = deck.facedown_stack.set(cards=facedown_cards)
    deck = deck.set(discard_faceup_stack=discard_faceup_stack, facedown_stack=facedown_stack)

    facedown_cards = deck.facedown_stack.cards
    discard_facedown_cards = deck.discard_facedown_stack.cards
    while len(discard_facedown_cards) > 0:
        card = discard_facedown_cards[-1]
        discard_facedown_cards = discard_facedown_cards[:-1]
        facedown_cards = facedown_cards.append(card)
    discard_facedown_stack = deck.discard_facedown_stack.set(cards=discard_facedown_cards)
    facedown_stack = deck.facedown_stack.set(cards=facedown_cards)
    deck = deck.set(discard_facedown_stack=discard_facedown_stack, facedown_stack=facedown_stack)

    deck = shuffle(kernel.rng, deck)
    kernel = set_deck(kernel, deck.idx, deck)
    kernel = flip_cards(kernel, deck.idx, num_faceup_spots)
    return kernel


@dispatch(State, Action2)
def handle_faceup_draw_action(kernel, action):
    if not kernel or not action or not action.legal_action or not action.legal_action.faceup_draw:
        return kernel
    legal_action = action.legal_action
    faceup_draw = legal_action.faceup_draw
    player = kernel.players[legal_action.player_idx]
    deck = kernel.deck_statuses[faceup_draw.deck_idx]
    # find the faceup spot idx with uuid "faceup_draw.card_name"
    spot_idx = next((i for i, card_name in enumerate(deck.faceup_spread.spots) if card_name == faceup_draw.card_name), None)
    drawn_card = deck.faceup_spread.spots[spot_idx] if spot_idx is not None else None
    player_cards = player.cards.append(drawn_card)
    player = player.set(cards=player_cards)
    players = kernel.players.set(legal_action.player_idx, player)
    kernel = kernel.set(players=players)
    spots = deck.faceup_spread.spots.set(spot_idx, None)
    faceup_spread = deck.faceup_spread.set(spots=spots)
    deck = deck.set(faceup_spread=faceup_spread)
    decks = kernel.deck_statuses.set(faceup_draw.deck_idx, deck)
    kernel = kernel.set(deck_statuses=decks)
    kernel = recycle_decks_if_needed(kernel)
    kernel = replenish_faceup_spot_if_needed(kernel, faceup_draw.deck_idx, spot_idx)
    return kernel


@dispatch(State, Action2)
def handle_after_move_pieces_to_path_action(kernel, action):
    kernel = handle_move_bonus_cards(kernel, action)
    return kernel


@dispatch(State, Action2)
def handle_move_bonus_cards(kernel, action):
    return handle_move_longest_path_card(kernel, action)


# Take a random walk on the player's graph. A node can be visiting more than once, but an edge cannot be visited more than once.
# Example graph: PlayerGraph(player_idx=0, neighbors=[[], [], [], [], [], [], [], [], [], [], [30]
@dispatch(State, int)
def random_player_graph_walk(kernel, player_idx):
    player_graph = kernel.players[player_idx].graph
    nodes_indices_with_neighbors = [i for i, neighbors in enumerate(player_graph.neighbors) if neighbors]
    
    if not nodes_indices_with_neighbors:
        return None
    
    rng = kernel.rng
    random_start_node_idx = rng.choice(nodes_indices_with_neighbors)

    def choose_next_node(visited_nodes, visited_edges):
        current_node_idx = visited_nodes[-1]
        neighbors = player_graph.neighbors[current_node_idx]
        if not neighbors:
            return None
        
        shuffled_neighbors = neighbors.copy()
        rng.shuffle(shuffled_neighbors)
        
        for neighbor in shuffled_neighbors:
            edge = (min(current_node_idx, neighbor), max(current_node_idx, neighbor))
            if edge not in visited_edges:
                return neighbor
        
        return None

    def walk(visited_nodes, visited_edges):
        next_node = choose_next_node(visited_nodes, visited_edges)
        if next_node is None:
            return (visited_nodes, visited_edges)
        next_edge = (min(visited_nodes[-1], next_node), max(visited_nodes[-1], next_node))
        return walk(
            visited_nodes + [next_node], 
            set(list(visited_edges) + [next_edge])
        )

    return walk([random_start_node_idx], set([]))


@dispatch(State, int)
def random_player_graph_walk3(kernel, player_idx):
    player_graph = kernel.players[player_idx].graph
    nodes_indices_with_neighbors = [i for i, neighbors in enumerate(player_graph.neighbors) if neighbors]

    if not nodes_indices_with_neighbors:
        return None

    rng = kernel.rng
    random_start_node_idx = rng.choice(nodes_indices_with_neighbors)

    def choose_next_node(visited_nodes, visited_edges):
        current_node_idx = visited_nodes[-1]
        neighbors = player_graph.neighbors[current_node_idx]
        if not neighbors:
            return None

        # Find unvisited edges (neighbors we haven't traversed to yet)
        unvisited_neighbors = [
            neighbor for neighbor in neighbors
            if (min(current_node_idx, neighbor), max(current_node_idx, neighbor)) not in visited_edges
        ]

        if not unvisited_neighbors:
            return None

        # Randomly choose one unvisited neighbor (no shuffle needed)
        return rng.choice(unvisited_neighbors)

    def walk(visited_nodes, visited_edges):
        next_node = choose_next_node(visited_nodes, visited_edges)
        if next_node is None:
            return (visited_nodes, visited_edges)
        next_edge = (min(visited_nodes[-1], next_node), max(visited_nodes[-1], next_node))
        return walk(
            visited_nodes + [next_node],
            set(list(visited_edges) + [next_edge])
        )

    return walk([random_start_node_idx], set([]))


@dispatch(State)
def find_player_with_longest_path(kernel):
    longest_path_player_idx = None
    longest_path_length = 0

    for player_idx in range(kernel.game_config.num_players):
        path_length = get_longest_path_length3(kernel, player_idx)
        if path_length > longest_path_length:
            longest_path_length = path_length
            longest_path_player_idx = player_idx

    if longest_path_player_idx is None:
        return None
    
    return kernel.players[longest_path_player_idx]


@dispatch(State, set)
def calc_path_len_from_edges3(kernel, edge_tuples):
    if edge_tuples is None:
        return 0
    edge_lens = v()
    for edge_tuple in edge_tuples:
        edge_idx = kernel.game_config.fig.edgetuple2idx[edge_tuple]
        if edge_idx is not None:
            edge = kernel.game_config.fig.edges[edge_idx]
            if edge and edge.paths:
                path_idxs = [p.idx for p in edge.paths]
                first_path_idx = path_idxs[0]
                first_path = kernel.game_config.fig.paths[first_path_idx]
                segment_idxs = [s.idx for s in first_path.segments]
                edge_len = len(segment_idxs)
                edge_lens = edge_lens.append(edge_len)

    return sum(edge_lens)


@dispatch(State, int)
def get_longest_path_length3(kernel, player_idx):
    longest_path_length = 0
    num_iters_since_change = 0

    for _ in range(NUM_RANDOM_WALKS):
        walk = random_player_graph_walk3(kernel, player_idx)
        if not walk:
            return 0
        path_len = calc_path_len_from_edges3(kernel, walk[1])
        if path_len > longest_path_length:
            longest_path_length = path_len
            num_iters_since_change = 0
        else:
            num_iters_since_change += 1
        # If we haven't found a longer path in 500 iterations, return
        if num_iters_since_change > 250:
            return longest_path_length

    # print("longest_path_length: ", longest_path_length)
    return longest_path_length


@dispatch(State, Action2)
def handle_move_longest_path_card(kernel, action):
    player = find_player_with_longest_path(kernel)

    if not kernel or not player:
        return kernel

    longest_path_card = None

    if len(kernel.deck_statuses) > 2:
        longest_path_deck = kernel.deck_statuses[2]
        if longest_path_deck.facedown_stack.cards:
            # Move the longest path card to the player's hand
            longest_path_card = longest_path_deck.facedown_stack.cards[-1]
            facedown_cards = longest_path_deck.facedown_stack.cards[:-1]
            facedown_stack = longest_path_deck.facedown_stack.set(cards=facedown_cards)
            longest_path_deck = longest_path_deck.set(facedown_stack=facedown_stack)
            decks = kernel.deck_statuses.set(2, longest_path_deck)
            kernel = kernel.set(deck_statuses=decks)
        else:
            # Search for the longest path card in each player's cards
            player_with_card = find_player_with_longest_path_card(kernel)
            if player_with_card:
                # Find the index of the card from the player's cards, then pop it
                card_idx = next((i for i, card_name in enumerate(player_with_card.cards) if getcardfromname(kernel, card_name).deck_idx == 2), None)
                if card_idx is not None:
                    longest_path_card = player_with_card.cards[card_idx]
                    player_with_card_cards = player_with_card.cards[:card_idx] + player_with_card.cards[card_idx+1:]
                    player_with_card = player_with_card.set(cards=player_with_card_cards)
                    player_with_card_idx = next((i for i, p in enumerate(kernel.players) if p.idx == player_with_card.idx), None)
                    if player_with_card_idx is not None:
                        players = kernel.players.set(player_with_card_idx, player_with_card)
                        kernel = kernel.set(players=players)


    if longest_path_card:
        player_cards = player.cards.append(longest_path_card)
        player = player.set(cards=pvector(set(player_cards)))
        player_idx = next((i for i, p in enumerate(kernel.players) if p.idx == player.idx), None)
        if player_idx is not None:
            players = kernel.players.set(player_idx, player)
            kernel = kernel.set(players=players)

    return kernel

@dispatch(State)
def find_player_with_longest_path_card(kernel):
    for player in kernel.players:
        if any(getcardfromname(kernel, card_name).deck_idx == 2 for card_name in player.cards):
            return player
    return None


@dispatch(State, Action2)
def handle_move_pieces_to_path_action(kernel, action):
    if not kernel or not action or not action.legal_action or not action.legal_action.move_pieces_to_path:
        return kernel
    
    legal_action = action.legal_action
    move_pieces_to_path = legal_action.move_pieces_to_path
    default = move_pieces_to_path.default
    override = action.move_pieces_to_path
    if override:
        default = default.set(piece_names=override.piece_names)
        default = default.set(card_names=override.card_names)

    player = kernel.players[legal_action.player_idx]
    if not player or not player.pieces:
        return kernel

    path_name = move_pieces_to_path.path
    # parse path name such as "edge-15-path-1"
    edge_idx = int(path_name.split("-")[1])
    path_idx_of_edge = int(path_name.split("-")[3])
    edge = kernel.edges[edge_idx]
    path = edge.paths[path_idx_of_edge]


    segment_idxs = [s.idx for s in path.segments]

    if path is None or not segment_idxs:
        return kernel

    segment_records = kernel.segment_records
    player_pieces = player.pieces
    for piece_name, segment_idx in zip(default.piece_names, segment_idxs):
        segment_record = segment_records[segment_idx]
        # Find the piece in the player's pieces
        piece_idx = next((i for i, player_piece_name in enumerate(player_pieces) if player_piece_name == piece_name), None)
        if piece_idx is not None:
            # Remove the piece from player's pieces
            piece = player_pieces[piece_idx]
            player_pieces = player_pieces[:piece_idx] + player_pieces[piece_idx+1:]
            segment_piece_names = segment_record.piece_names.append(piece)
            segment_record = segment_record.set(piece_names=segment_piece_names)
            segment_records = segment_records.set(segment_idx, segment_record)

    kernel = kernel.set(segment_records=segment_records)

    player = player.set(
        pieces=player_pieces,
        graph=calc_player_graph3(
            kernel.game_config,
            kernel.segment_records,
            player.idx,
        )
    )

    player_cards = player.cards
    decks = kernel.deck_statuses
    for card_name in default.card_names:
        # Find the card in the player's cards
        card_idx = next((i for i, player_card_name in enumerate(player_cards) if player_card_name == card_name), None)
        if card_idx is not None:
            # Remove the card from player's cards
            card_name = player_cards[card_idx]
            player_cards = player_cards[:card_idx] + player_cards[card_idx+1:]
            # add to discard
            deck_idx = getcardfromname(kernel, card_name).deck_idx
            deck = decks[deck_idx]
            discard_cards = deck.discard_faceup_stack.cards.append(card_name)
            discard_faceup_stack = deck.discard_faceup_stack.set(cards=discard_cards)
            deck = deck.set(discard_faceup_stack=discard_faceup_stack)
            decks = decks.set(deck_idx, deck)
    player = player.set(cards=player_cards)
    kernel = kernel.set(deck_statuses=decks)
    kernel = recycle_decks_if_needed(kernel)
    kernel = replenish_decks_if_needed(kernel)
    players = kernel.players.set(legal_action.player_idx, player)
    kernel = kernel.set(players=players)
    
    if False: # path.idx == 15:
        print("\n")
        print("handle_move_pieces_to_path_action: segment_record.piece_names =", segment_record.piece_names)
        print("handle_move_pieces_to_path_action: path.segments =", path.segments)
        print("\n")
    
    segment_idx_of_path = None
    for segment_idx, segment in enumerate(path.segments):
        if segment.idx == segment_record.segment_idx:
            segment_idx_of_path = segment_idx
            break
    
    segment = path.segments[segment_idx_of_path]

    updated_segments = path.segments.set(
        segment_idx_of_path, 
        segment.set(piece_names=segment_record.piece_names)
    )
    
    if False: # path.idx == 15:
        print("\n")
        print("handle_move_pieces_to_path_action: updated_segments =", updated_segments)
        print("\n")

    updated_path = path.set(segments=pvector(updated_segments))
    updated_paths = edge.paths.set(
        path_idx_of_edge, 
        updated_path,
    )
    updated_edge = edge.set(paths=updated_paths)
    updated_edges = kernel.edges.set(
        path.edge_idx,
        updated_edge,
    )
    kernel = kernel.set(edges=updated_edges)

    if False: # path.idx == 15:
        print("handle_move_pieces_to_path_action: updated edge.paths[15] =", updated_edge.paths)
        print("\n")

    return kernel


# @dispatch(GameConfig, PVector, int)
def calc_player_graph3(game_config, segment_records, player_idx, log=False):
    node2neighbors = {node.idx: set() for node in game_config.fig.nodes}

    for edge in game_config.fig.edges:
        for path in edge.paths:
            segment_idxs = [s.idx for s in path.segments]
            for segment_idx in segment_idxs:
                segment_record = segment_records[segment_idx]
                if segment_record.piece_names:
                    first_piece = getpiecefromname(game_config, segment_record.piece_names[0])
                    if first_piece.player_idx == player_idx:
                        if log:
                            print(f"[path_idx {path.idx}] edge.start_point_uuid {edge.start_point_uuid} ({edge.node_1_idx}) connected to edge.end_point_uuid {edge.end_point_uuid} ({edge.node_2_idx}) player_idx: {player_idx}")
                        node2neighbors[edge.node_1_idx].add(edge.node_2_idx)
                        node2neighbors[edge.node_2_idx].add(edge.node_1_idx)
    
    # Build and adjacency matrix
    adjacency_matrix = [
        [0 for _ in range(len(game_config.fig.nodes))]
        for _ in range(len(game_config.fig.nodes))
    ]
    for node_idx, neighbors in node2neighbors.items():
        for neighbor_idx in neighbors:
            adjacency_matrix[node_idx][neighbor_idx] = 1
            adjacency_matrix[neighbor_idx][node_idx] = 1  # Undirected graph

    neighbors = pvector([
        pvector(node2neighbors.get(node_idx, set()))
        for node_idx in range(len(game_config.fig.nodes))
    ])
    
    return PlayerGraph(
        player_idx=player_idx,
        neighbors=neighbors,
        claimed_edges_adjacency_matrix=pvector(adjacency_matrix),
    )


# Does the opposite of handle_discard_action, i.e., it keeps the cards in the discard tray (the other cards are discarded)
@dispatch(State, Action2)
def handle_keep_action(kernel, action):
    if not kernel or not action or not action.legal_action.keep:
        return kernel

    deck_idx = action.legal_action.keep.deck_idx
    if deck_idx < 0 or deck_idx >= len(kernel.deck_statuses):
        return kernel

    deck = kernel.deck_statuses[deck_idx]
    if not deck:
        return kernel

    player = kernel.players[action.legal_action.player_idx]
    if not player:
        return kernel
    
    kept_cards = v()
    non_kept_cards = v()
    discard_tray_idxs = action.keep.discard_tray_idxs
    for i, card_name in enumerate(player.discard_tray):
        if i in discard_tray_idxs:
            kept_cards = kept_cards.append(card_name)
        else:
            non_kept_cards = non_kept_cards.append(card_name)

    # Discard the non-kept cards to the deck's discard pile
    discard_cards = deck.discard_facedown_stack.cards.extend(non_kept_cards)
    discard_facedown_stack = deck.discard_facedown_stack.set(cards=discard_cards)
    deck = deck.set(discard_facedown_stack=discard_facedown_stack)

    # Clear the discard tray and add the kept cards back
    player_cards = player.cards.extend([c for c in kept_cards if c is not None])
    player = player.set(cards=player_cards, discard_tray=v())

    players = kernel.players.set(player.idx, player)
    decks = kernel.deck_statuses.set(deck_idx, deck)
    return kernel.set(deck_statuses=decks, players=players)


@dispatch(State, Action2)
def handle_discard_action(kernel, action):
    print("****************************** handle_discard_action 1", action)
    if not kernel or not action or not action.legal_action.discard:
        return kernel

    print("****************************** handle_discard_action 2", action)

    deck_idx = action.legal_action.discard.deck_idx
    if deck_idx < 0 or deck_idx >= len(kernel.deck_statuses):
        return kernel

    print("****************************** handle_discard_action 3", deck_idx)

    deck = kernel.deck_statuses[deck_idx]
    print("****************************** handle_discard_action 3.5", deck)
    if not deck:
        return kernel

    print("****************************** handle_discard_action 4")

    player = kernel.players[action.legal_action.player_idx]
    if not player:
        return kernel

    non_kept_cards = v()
    kept_cards = v()
    discard_tray_idxs = action.discard.discard_tray_idxs
    for i, card_name in enumerate(player.discard_tray):
        if i in discard_tray_idxs:
            non_kept_cards = non_kept_cards.append(card_name)
        else:
            kept_cards = kept_cards.append(card_name)

    print("****************************** handle_discard_action 5", kept_cards)
    print("****************************** handle_discard_action 6", non_kept_cards)

    # Discard the non-kept cards to the deck's discard pile
    discard_cards = deck.discard_facedown_stack.cards.extend(non_kept_cards)
    discard_facedown_stack = deck.discard_facedown_stack.set(cards=discard_cards)
    deck = deck.set(discard_facedown_stack=discard_facedown_stack)

    # Clear the discard tray and add the kept cards back
    player_cards = player.cards.extend([c for c in kept_cards if c is not None])
    player = player.set(cards=player_cards, discard_tray=v())
    print("****************************** handle_discard_action 10 kept_cards: ", kept_cards)

    players = kernel.players.set(player.idx, player)
    decks = kernel.deck_statuses.set(deck_idx, deck)
    return kernel.set(deck_statuses=decks, players=players)


@dispatch(State)
def shuffle_all_decks(kernel):
    if not kernel or not kernel.deck_statuses:
        return kernel

    for i in range(len(kernel.deck_statuses)):
        kernel = shuffle_deck(kernel, i)

    return kernel


@dispatch(State, int, DeckStatus)
def set_deck(kernel, deck_idx, deck):
    new_decks = kernel.deck_statuses[:deck_idx] + [deck] + kernel.deck_statuses[deck_idx + 1:]
    return kernel.set(deck_statuses=new_decks)


def shuffle(rng, deck):
    shuffled_cards = list(deck.facedown_stack.cards)
    rng.shuffle(shuffled_cards)
    return deck.set(facedown_stack=FacedownCardStack(cards=pvector(shuffled_cards)))


@dispatch(State, int)
def shuffle_deck(kernel, deck_idx):
    if not kernel or not kernel.deck_statuses or deck_idx < 0 or deck_idx >= len(kernel.deck_statuses):
        return kernel
    
    deck = kernel.deck_statuses[deck_idx]
    if not deck or not deck.facedown_stack.cards:
        return kernel

    shuffled_deck = shuffle(kernel.rng, deck)
    kernel = set_deck(kernel, deck_idx, shuffled_deck)
    return kernel


@dispatch(State)
def shuffle_player_order(kernel):
    if not kernel or not kernel.player_idxs:
        return kernel
    
    rng = kernel.rng
    shuffled_idxs = list(kernel.player_idxs)
    rng.shuffle(shuffled_idxs)

    return kernel.set(player_idxs=pvector(shuffled_idxs))


@dispatch(State, int, int)
def flip_cards(kernel, deck_idx, num_cards):
    if not kernel or deck_idx < 0 or deck_idx >= len(kernel.deck_statuses):
        return kernel
    
    deck = kernel.deck_statuses[deck_idx]
    if not deck or not deck.facedown_stack.cards:
        return kernel

    # Flip the top num_cards from the facedown_stack to the faceup_spread
    facedown_cards = deck.facedown_stack.cards
    faceup_spots = deck.faceup_spread.spots
    for _ in range(num_cards):
        if facedown_cards:
            card = facedown_cards[-1]
            facedown_cards = facedown_cards[:-1]
            faceup_spots = faceup_spots.append(card)
    facedown_stack = deck.facedown_stack.set(cards=facedown_cards)
    faceup_spread = deck.faceup_spread.set(spots=faceup_spots)
    deck = deck.set(facedown_stack=facedown_stack, faceup_spread=faceup_spread)
    decks = kernel.deck_statuses.set(deck_idx, deck)
    return kernel.set(deck_statuses=decks)


@dispatch(State)
def distribute_all_piles(kernel):
    if not kernel or not kernel.piles:
        return kernel

    players = kernel.players
    piles = kernel.piles
    for pile_idx, pile in enumerate(piles):
        player_idx = pile.player_idx
        if player_idx < 0 or player_idx >= len(players):
            continue

        player = players[player_idx]
        player_pieces = player.pieces.extend(pvector([x.name for x in pile.pieces]))
        player = player.set(pieces=player_pieces)
        players = players.set(player_idx, player)
        pile = pile.set(pieces=v(), num_pieces=0)
        piles = piles.set(pile_idx, pile)

    return kernel.set(players=players, piles=piles)


@dispatch(State, int, int)
def deal_cards_to_each_player_discard_tray(kernel, deck_idx, num_cards):
    if not kernel or deck_idx < 0 or deck_idx >= len(kernel.deck_statuses):
        return kernel

    deck = kernel.deck_statuses[deck_idx]
    if not deck or not deck.facedown_stack.cards:
        return kernel

    updated_players = v()
    facedown_cards = deck.facedown_stack.cards
    for player in kernel.players:
        # Deal cards to the player's discard tray
        discard_tray = player.discard_tray
        for _ in range(num_cards):
            if facedown_cards:
                card = facedown_cards[-1]
                facedown_cards = facedown_cards[:-1]
                discard_tray = discard_tray.append(card)
        player = player.set(discard_tray=discard_tray)
        updated_players = updated_players.append(player)
    facedown_stack = deck.facedown_stack.set(cards=facedown_cards)
    deck = deck.set(facedown_stack=facedown_stack)
    decks = kernel.deck_statuses.set(deck_idx, deck)
    return kernel.set(players=updated_players, deck_statuses=decks)


@dispatch(State, int, int)
def deal_cards_to_each_player(kernel, deck_idx, num_cards):
    if not kernel or deck_idx < 0 or deck_idx >= len(kernel.deck_statuses):
        return kernel

    deck = kernel.deck_statuses[deck_idx]
    if not deck or not deck.facedown_stack.cards:
        return kernel

    players = kernel.players
    facedown_cards = deck.facedown_stack.cards
    for player_idx, player in enumerate(players):
        player_hand = player.cards
        # Deal cards to the player's hand
        for _ in range(num_cards):
            if facedown_cards:
                card = facedown_cards[-1]
                facedown_cards = facedown_cards[:-1]
                player_hand = player_hand.append(card)
        player = player.set(cards=player_hand)
        players = players.set(player_idx, player)
    facedown_stack = deck.facedown_stack.set(cards=facedown_cards)
    deck = deck.set(facedown_stack=facedown_stack)
    decks = kernel.deck_statuses.set(deck_idx, deck)
    return kernel.set(players=players, deck_statuses=decks)


@dispatch(State, Action2)
def default_accept_action(state, action):

    # Returns true if action.legal_action is found in state.legal_actions
    # The comparision is by value, not by reference
    if action.legal_action not in state.legal_actions:
        return False, "Action not found in legal actions"

    # Check if "action.move_pieces_to_path" is not None
    if action.move_pieces_to_path:
        is_legal = is_move_pieces_to_path_action_legal(state, action)
        if not is_legal:
            return False, "Move pieces to path action is not legal"

    return True, "Action is legal"


@dispatch(State, Action2)
def is_move_pieces_to_path_action_legal(state, action):
    # print("******************************1234 is_move_pieces_to_path_action_legal 1")
    player_idx = action.legal_action.player_idx
    proposed_cards_uuids = action.move_pieces_to_path.card_names
    path_idx = action.legal_action.move_pieces_to_path.path_idx
    path = state.game_config.fig.paths[path_idx]
    proposed_cards = pvector([card_name for card_name in state.players[player_idx].cards if card_name in proposed_cards_uuids])
    proposed_pieces = pvector([piece_name for piece_name in state.players[player_idx].pieces if piece_name in action.move_pieces_to_path.piece_names])
    segment_idxs = [s.idx for s in path.segments]
    remaining_segment_records = pvector([state.segment_records[segment_idx] for segment_idx in segment_idxs])

    # print("******************************1234 is_move_pieces_to_path_action_legal 1b: ", proposed_cards)
    # print("******************************1234 is_move_pieces_to_path_action_legal 1c: ", proposed_pieces)
    # print("******************************1234 is_move_pieces_to_path_action_legal 1d: ", len(remaining_segments))

    card_fulfillment, piece_fulfillment = get_path_fulfillment_from_resources(
        state,
        proposed_cards,
        proposed_pieces,
        remaining_segment_records,
    )

    # print("******************************1234 is_move_pieces_to_path_action_legal 2a", card_fulfillment)
    # print("******************************1234 is_move_pieces_to_path_action_legal 2b", piece_fulfillment)

    if card_fulfillment is None or piece_fulfillment is None:
        return False

    # print("******************************1234 is_move_pieces_to_path_action_legal 3")
    # print("******************************1234 is_move_pieces_to_path_action_legal piece_fulfillment: ", piece_fulfillment)
    # print("******************************1234 is_move_pieces_to_path_action_legal proposed_pieces: ", proposed_pieces)

    return (
        len(card_fulfillment) == len(proposed_cards_uuids) and
        len(piece_fulfillment) == len(proposed_pieces)
    )


@dispatch(State)
def get_total_path_count(kernel):
    return len(kernel.game_config.fig.paths)


@dispatch(State, int, int)
def get_legal_actions_for_path(state_kernel, player_idx, path_idx):
    
    if path_idx < 0 or get_total_path_count(state_kernel) <= path_idx:
        return v()

    if not is_path_open_to_player(state_kernel, path_idx, player_idx):
        return v()

    legal_actions = v()
    default = get_sample_actionclaimpath(state_kernel, player_idx, path_idx)
    path = state_kernel.game_config.fig.paths[path_idx]
    if default:
        legal_actions = legal_actions.append(
            init_legal_action(
                player_idx=player_idx,
                name="CLAIM-PATH",
                title="Select resources to claim path",
                instruction="claim a path",
                allotted_seconds=DEFAULT_ALLOTTED_SECONDS,
                allotted_since_action_idx=(len(state_kernel.history) - 1),
                btn_text="Claim path",
                move_pieces_to_path=LegalActionMovePiecesToPath(
                    path=path.name,
                    default=default
                )
            )
        )
        return legal_actions

    return v()


@dispatch(State, int)
def get_legal_actions_for_paths(kernel, player_idx):
    legal_actions = v()
    
    for path_idx in range(get_total_path_count(kernel)):
        legal_actions_for_path = get_legal_actions_for_path(kernel, player_idx, path_idx)
        if legal_actions_for_path:
            legal_actions = legal_actions.extend(legal_actions_for_path)
        # else:
        #     print(f"Path {path_idx} is not claimable by player {player_idx}")
    
    return legal_actions


@dispatch(State, Edge)
def get_player_idxs_on_edge(kernel, edge):
    player_idxs = set()
    if not edge or not edge.paths:
        return list(player_idxs)
    
    for path in edge.paths:
        segment_idxs = [s.idx for s in path.segments]
        for segment_idx in segment_idxs:
            segment = kernel.segment_records[segment_idx]
            if segment.piece_names and segment.piece_names[0]:
                piece = getpiecefromname(kernel, segment.piece_names[0])
                if piece:
                    player_idxs.add(piece.player_idx)
    
    return list(player_idxs)

@dispatch(State, int, int)
def is_path_open_to_player(state_kernel, path_idx, player_idx):

    if not state_kernel or path_idx < 0 or get_total_path_count(state_kernel) <= path_idx:
        return False
    
    path = state_kernel.game_config.fig.paths[path_idx]
    edge = state_kernel.game_config.fig.edges[path.edge_idx]
    segment_idxs = [s.idx for s in path.segments]

    player_idxs_on_edge = get_player_idxs_on_edge(state_kernel, edge)

    # Check if edge is too crowded for the number of players
    if state_kernel.game_config.num_players <= 3:
        if len(player_idxs_on_edge) > 0:
            return False
        
    if player_idx in player_idxs_on_edge:
        return False
    
    # Check if any segment of the path has pieces from any player
    for segment_idx in segment_idxs:
        segment_record = state_kernel.segment_records[segment_idx]
        if segment_record.piece_names:
            return False

    # Check if the player has enough pieces to claim the path
    player_pieces = state_kernel.players[player_idx].pieces
    if len(player_pieces) < len(segment_idxs):
        return False
    
    return True


HOOK_NAMESPACE = {
    'INITIAL_ALLOTTED_SECONDS': INITIAL_ALLOTTED_SECONDS,
    'DEFAULT_ALLOTTED_SECONDS': DEFAULT_ALLOTTED_SECONDS,
    'shuffle_all_decks': shuffle_all_decks,
    'shuffle_player_order': shuffle_player_order,
    'deal_cards_to_each_player': deal_cards_to_each_player,
    'deal_cards_to_each_player_discard_tray': deal_cards_to_each_player_discard_tray,
    'distribute_all_piles': distribute_all_piles,
    'flip_cards': flip_cards,
    'LegalActionDiscard': LegalActionDiscard,
    'LegalActionKeep': LegalActionKeep,
    'default_handle_action': default_handle_action,
    'handle_discard_action': handle_discard_action,
    'handle_keep_action': handle_keep_action,
    'handle_move_pieces_to_path_action': handle_move_pieces_to_path_action,
    'handle_after_move_pieces_to_path_action': handle_after_move_pieces_to_path_action,
    'handle_move_bonus_cards': handle_move_bonus_cards,
    'handle_move_longest_path_card': handle_move_longest_path_card,
    'find_player_with_longest_path_card': find_player_with_longest_path_card,
    'default_after_accept_action': default_after_accept_action,
    'default_accept_action': default_accept_action,
    'LegalAction': LegalAction,
    'LegalActionDraw': LegalActionDraw,
    'LegalActionDrawDiscard': LegalActionDrawDiscard,
    'LegalActionFaceupDraw': LegalActionFaceupDraw,
    'LegalActionMovePiecesToPath': LegalActionMovePiecesToPath,
    'get_legal_actions_for_paths': get_legal_actions_for_paths,
    'get_legal_actions_for_path': get_legal_actions_for_path,
    'is_path_open_to_player': is_path_open_to_player,
    'ActionMovePiecesToPath': ActionMovePiecesToPathOptional,
}


def get_wild_unit_uuids(decks):
    wild_unit_uuids = set()
    for deck in decks:
        for card in deck.cards:
            if card.is_wild:
                wild_unit_uuids.add(card.resource_uuid)
    return pvector(wild_unit_uuids)


@dispatch(State, int)
def getsegment(k, segment_idx):
    return k.game_config.fig.segments[segment_idx]


@dispatch(State, PVector, PVector, PVector)
def match_strict_wild(k, fulfillment, cards, segment_records):
    new_fulfillment = pvector(fulfillment)
    new_cards = pvector(cards)
    wild_unit_uuids = k.game_config.wild_unit_uuids
    new_segment_records = v()

    for segment_record in segment_records:
        segment = getsegment(k, segment_record.segment_idx)
        if segment.unit_uuid and segment.unit_uuid in wild_unit_uuids:
            first_matching_idx = next((i for i, card_name in enumerate(new_cards) if getcardfromname(k, card_name).resource_uuid == segment.unit_uuid), None)
            if first_matching_idx is not None:
                # Remove the matched card from new_cards and add it to fulfillment
                matched_card = new_cards[first_matching_idx]
                new_fulfillment = new_fulfillment.append(matched_card)
                new_cards = new_cards[:first_matching_idx] + new_cards[first_matching_idx + 1:]
            else:
                new_segment_records = new_segment_records.append(segment_record)
        else:
            new_segment_records = new_segment_records.append(segment_record)

    return new_fulfillment, new_cards, new_segment_records

@dispatch(State, PVector, PVector, PVector)
def match_non_wild_non_empty(k, fulfillment, cards, segment_records):
    new_fulfillment = pvector(fulfillment)
    new_cards = pvector(cards)
    wild_unit_uuids = k.game_config.wild_unit_uuids
    new_segment_records = v()

    for segment_record in segment_records:
        segment = getsegment(k, segment_record.segment_idx)
        first_strict_matching_idx = next((i for i, card_name in enumerate(new_cards) if getcardfromname(k, card_name).resource_uuid == segment.unit_uuid), None)
        first_wild_matching_idx = next((i for i, card_name in enumerate(new_cards) if getcardfromname(k, card_name).resource_uuid in wild_unit_uuids), None)
        first_matching_idx = first_strict_matching_idx if first_strict_matching_idx is not None else first_wild_matching_idx
        if first_matching_idx is not None:
            # Remove the matched card from new_cards and add it to fulfillment
            matched_card = new_cards[first_matching_idx]
            new_fulfillment = new_fulfillment.append(matched_card)
            new_cards = new_cards[:first_matching_idx] + new_cards[first_matching_idx + 1:]
        else:
            new_segment_records = new_segment_records.append(segment_record)

    return new_fulfillment, new_cards, new_segment_records

    
@dispatch(State, PVector, PVector, PVector)
def match_empty(k, fulfillment, cards, segment_records):
    num_empty_segment_records = sum(1 for segment_record in segment_records if getsegment(k, segment_record.segment_idx).unit_uuid is None)
    if num_empty_segment_records == 0:
        return fulfillment, cards, segment_records
    
    tuples = get_uniform_sets(k, cards, num_empty_segment_records)
    # print(f"****************************************** len(cards): {len(cards)}")
    # print(f"****************************************** num_empty_segments: {num_empty_segments}")
    # print(f"Found {len(tuples)} tuples for empty segments: {tuples}")
    if len(tuples) == 0:
        return fulfillment, cards, segment_records
    
    new_fulfillment = pvector(fulfillment)

    new_segment_records = v()
    for segment_record in segment_records:
        segment = getsegment(k, segment_record.segment_idx)
        if segment.unit_uuid:
            new_segment_records = new_segment_records.append(segment_record)

    first_tuple = tuples[0][:num_empty_segment_records]
    # print(f"Using first tuple for empty segments: {first_tuple}")
    new_cards = list(set(cards) - set(first_tuple))
    new_fulfillment = new_fulfillment.extend(first_tuple)
    return new_fulfillment, new_cards, new_segment_records


@dispatch(State, PVector, int)
def get_uniform_sets(state_kernel, cards, min_length):
    wilds = [card_name for card_name in cards if getcardfromname(state_kernel, card_name).is_wild]
    non_wilds = [card_name for card_name in cards if not getcardfromname(state_kernel, card_name).is_wild]
    # print("********************* cards: ", cards)
    # print("********************* wilds: ", wilds)
    # print("********************* non_wilds: ", non_wilds)
    unit_uuid_2_cards = {}
    for card_name in non_wilds:
        card = getcardfromname(state_kernel, card_name)
        if card.resource_uuid not in unit_uuid_2_cards:
            unit_uuid_2_cards[card.resource_uuid] = []
        unit_uuid_2_cards[card.resource_uuid].append(card_name)
    
    uniform_sets_no_wilds = [
        card_names for card_names in unit_uuid_2_cards.values() if len(card_names) >= min_length
    ]
    # print("********************* uniform_sets_no_wilds: ", uniform_sets_no_wilds)
    # print("********************* length: ", min_length)
    # print("********************* unit_uuid_2_cards.values(): ", unit_uuid_2_cards.values())

    uniform_sets_with_wilds = []
    for num_wilds in range(0, len(wilds)+1):
        uniform_set = wilds[:num_wilds]
        if len(uniform_set) >= min_length:
            uniform_sets_with_wilds.append(uniform_set)
        for unit_uuid, cards in unit_uuid_2_cards.items():
            uniform_set = cards + wilds[:num_wilds]
            if len(uniform_set) >= min_length:
                uniform_sets_with_wilds.append(uniform_set)

    # Sort the uniform sets by their length, smallest first
    uniform_sets_no_wilds.sort(key=len)
    uniform_sets_with_wilds.sort(key=len)
    # print("********************* uniform_sets_no_wilds 2: ", uniform_sets_no_wilds)
    sorted = uniform_sets_no_wilds + uniform_sets_with_wilds
    # print("********************* sorted : ", sorted)
    # Filter out sets that are smaller than the required length
    return sorted


def does_fulfill_path(game, player_idx, path_idx, fulfillment):
    return False


@dispatch(State, int, int)
def get_sample_actionclaimpath(kernel, player_idx, path_idx):
    card_fulfillment, piece_fulfillment = get_sample_path_fulfillment(kernel, player_idx, path_idx)
    if not card_fulfillment or not piece_fulfillment:
        return None

    return ActionMovePiecesToPathOptional(
        piece_names=pvector([piece_name for piece_name in piece_fulfillment]),
        card_names=card_fulfillment,
    )

@dispatch(State, int, int)
def get_sample_path_fulfillment(kernel, player_idx, path_idx):
    path = kernel.game_config.fig.paths[path_idx]
    remaining_card_names = pvector([card_name for card_name in kernel.players[player_idx].cards if getcardfromname(kernel, card_name).deck_idx == 0])
    remaining_pieces = pvector([
        piece_name 
        for piece_name in kernel.players[player_idx].pieces 
        if getpiecefromname(kernel, piece_name).piece_template_idx == 0
    ])
    segment_idxs = [s.idx for s in path.segments]
    remaining_segment_records = pvector([kernel.segment_records[segment_idx] for segment_idx in segment_idxs])
    return get_path_fulfillment_from_resources(
        kernel,
        remaining_card_names,
        remaining_pieces,
        remaining_segment_records,
    )

@dispatch(State, PVector, PVector, PVector)
def get_path_fulfillment_from_resources(state_kernel, remaining_card_names, remaining_pieces, remaining_segment_records, log=False):

    if len(remaining_pieces) < len(remaining_segment_records):
        print("Not enough pieces to fulfill the path segments")
        return None, None
    
    piece_fulfillment = remaining_pieces[:len(remaining_segment_records)]

    card_fulfillment = v()
    card_fulfillment, remaining_card_names, remaining_segment_records = match_strict_wild(state_kernel, card_fulfillment, remaining_card_names, remaining_segment_records)

    if len(remaining_segment_records) == 0:
        return card_fulfillment, piece_fulfillment
    # Probably don't need this check, but we should unit test
    # elif len(get_wild_segments(remaining_segments)) > 0:
    #     return None

    card_fulfillment, remaining_card_names, remaining_segment_records = match_non_wild_non_empty(state_kernel, card_fulfillment, remaining_card_names, remaining_segment_records)
    if len(remaining_segment_records) == 0:
        return card_fulfillment, piece_fulfillment
    # Probably don't need this check, but we should unit test
    # elif len(get_non_wild_non_empty_segments(remaining_segments)) > 0:
    #     return None

    card_fulfillment, remaining_card_names, remaining_segment_records = match_empty(state_kernel, card_fulfillment, remaining_card_names, remaining_segment_records)
    if len(remaining_segment_records) == 0:
        return card_fulfillment, piece_fulfillment

    # print("get_path_fulfillment_from_resources (None, None) because remaining_segments is not empty: ", remaining_segments)
    return None, None


def run_state_action_hook(state, action, hook, log=False):

    # Clone HOOK_NAMESPACE
    namespace = HOOK_NAMESPACE.copy()

    try:
        # Execute the code string
        exec(hook.code, namespace)

        # Retrieve the handler function
        handler_func = namespace.get('handler')
        
        if handler_func is None or not callable(handler_func):
            raise ValueError("No callable function named 'handler' found in the code")
        
        # Call the handler function
        result = handler_func(state, action)
        if log:
            pass
            # print(f"****************************** Running initialization hook 3: {hook.uuid} {result.player_idxs}")
            # print(f"****************************** Result of handler(5, 3): {result}")
        return result

    except SyntaxError as e:
        msg = f"Syntax error in initialization hook {hook.uuid}: {str(e)}"
        logging.error(msg, exc_info=True)
        raise SyntaxError(msg) from e
    except Exception as e:
        msg = f"Error in initialization hook {hook.uuid}: {str(e)}"
        logging.error(msg, exc_info=True)
        raise Exception(msg) from e


def run_state_hook(state, hook, log=False):

    namespace = HOOK_NAMESPACE.copy()

    try:
        # Execute the code string
        exec(hook.code, namespace)
        
        # Retrieve the handler function
        handler_func = namespace.get('handler')
        
        if handler_func is None or not callable(handler_func):
            raise ValueError("No callable function named 'handler' found in the code")
        
        # Call the handler function
        result = handler_func(state)
        # if log:
        #     print(f"****************************** Running initialization hook 3: {hook.uuid} {result.player_idxs}")
            # print(f"****************************** Result of handler(5, 3): {result}")
        return result

    except SyntaxError as e:
        msg = f"Syntax error in initialization hook {hook.uuid}: {str(e)}"
        logging.error(msg, exc_info=True)
        raise SyntaxError(msg) from e
    except Exception as e:
        msg = f"Error in initialization hook {hook.uuid}: {str(e)}"
        logging.error(msg, exc_info=True)
        raise Exception(msg) from e


def run_kernel_hook(kernel, hook, log=False):

    namespace = HOOK_NAMESPACE.copy()

    try:
        # Execute the code string
        exec(hook.code, namespace)
        
        # Retrieve the handler function
        handler_func = namespace.get('handler')
        
        if handler_func is None or not callable(handler_func):
            raise ValueError("No callable function named 'handler' found in the code")
        
        # Call the handler function
        result = handler_func(kernel)
        # if log:
        #     print(f"****************************** Running initialization hook 3: {hook.uuid} {result.player_idxs}")
            # print(f"****************************** Result of handler(5, 3): {result}")
        return result

    except SyntaxError as e:
        msg = f"Syntax error in initialization hook {hook.uuid}: {str(e)}"
        logging.error(msg, exc_info=True)
        raise SyntaxError(msg) from e
    except Exception as e:
        msg = f"Error in initialization hook {hook.uuid}: {str(e)}"
        logging.error(msg, exc_info=True)
        raise Exception(msg) from e


# Implementing the following Julia function:
# function getfaceupspots(f, unit_deck, unit_deck_idx)
#     num_faceup_spots = getsettingvalue(f, :num_faceup_spots)
#     unit_deck[unit_deck_idx:(unit_deck_idx+(num_faceup_spots - 1))]
# end
def getfaceupspots(f, unit_deck, unit_deck_idx):
    num_faceup_spots = getsettingvalue(f, 'num_faceup_spots')
    if num_faceup_spots is None:
        raise ValueError("Setting 'num_faceup_spots' not found in board config.")
    return unit_deck[unit_deck_idx:(unit_deck_idx + num_faceup_spots)] if unit_deck_idx < len(unit_deck) else []


# Implementing the following Julia function:
# getpath(f::Fig, num::Int) = f.board_config.board_paths[num]
def getpath(f, num):
    if f and f.board_config and num < len(f.board_config.board_paths):
        return f.board_config.board_paths[num]
    raise ValueError(f"Path number {num} not found in board config.")







def isactionlegal2(s, a):
    return run_accept_action_hooks(s, a, ACCEPT_ACTION_HOOKS, False)


def calc_legal_actions3(state_kernel):
    history = state_kernel.history
    last_action = history[-1] if len(history) > 0 else None

    if last_action is None or last_action.legal_action.name == "INITIAL-KEEP-GOAL-CARDS":

        yet_to_make_initial_move = [
            player for player in state_kernel.players if len(player.discard_tray) > 0
        ]
        
        if len(yet_to_make_initial_move) == 0:
            # All players have made their initial move, proceed to the first player's turn
            return get_default_legal_actions(state_kernel, state_kernel.player_idxs[0])

        return pvector([
            init_legal_action(
                player_idx=player.idx,
                name="INITIAL-KEEP-GOAL-CARDS",
                instruction="Your move. Please select the routes you want to keep.",
                allotted_seconds=INITIAL_ALLOTTED_SECONDS,
                allotted_since_action_idx=(len(history) - 1),
                keep=LegalActionKeep(
                    deck_idx=1,
                    min=2,
                )
            )
            for player in yet_to_make_initial_move
        ])
    
    elif last_action.legal_action.faceup_draw:
        faceup_draw = last_action.legal_action.faceup_draw
        if not getcardfromname(state_kernel, faceup_draw.card_name).is_wild:
            legal_actions = get_follow_up_draw_legal_actions(state_kernel, last_action)
            if legal_actions:
                return legal_actions
    
    elif last_action.legal_action.draw:
        if last_action.legal_action.draw.quantity == 1:
            legal_actions = get_follow_up_draw_legal_actions(state_kernel, last_action)
            if legal_actions:
                return legal_actions
    
    elif last_action.legal_action.draw_discard:
        draw_discard = last_action.legal_action.draw_discard
        player = state_kernel.players[last_action.legal_action.player_idx]
        return pvector([
            init_legal_action(
                player_idx=player.idx,
                name="KEEP-GOAL-CARDS",
                instruction="Your move. Please select the routes you want to keep.",
                allotted_seconds=INITIAL_ALLOTTED_SECONDS,
                allotted_since_action_idx=(len(state_kernel.history) - 1),
                keep=LegalActionKeep(
                    deck_idx=draw_discard.deck_idx,
                    min=draw_discard.min,
                    max=draw_discard.max,
                )
            )
        ])
    
    if state_kernel.last_to_play == last_action.legal_action.player_idx:
        return v()
    
    next_player_idx = get_next_player_shuffled_idx(state_kernel, last_action)
    return get_default_legal_actions(state_kernel, state_kernel.player_idxs[next_player_idx])


def get_next_player_shuffled_idx(state_kernel, last_action):
    last_player_idx = last_action.legal_action.player_idx
    last_player_shuffled_idx = state_kernel.player_idxs.index(last_player_idx)
    next_player_shuffled_idx = (last_player_shuffled_idx + 1) % len(state_kernel.player_idxs)
    return next_player_shuffled_idx


def getnextstate2(s, a, log=False):
    is_legal, reason = isactionlegal2(s, a)
    if not is_legal:
        print("****************************** Action is not legal: ", json.dumps(a.__todict__(), indent=2))
        print("a")
        print("json.dumps(s.legal_actions): ", json.dumps([la.__todict__() for la in s.legal_actions], indent=2))
        print("b")
        print("\n\n")
        raise ValueError(f"Action is not legal: {a}. Reason: {reason}")
    kernel = s
    kernel = run_state_action_hooks(kernel, a, AFTER_ACCEPT_ACTION_HOOKS, log)
    kernel = run_state_action_hooks(kernel, a, HANDLE_ACTION_HOOKS, log)
    return init_memoized_state(kernel)


@dispatch(State, object)
def getpublicplayerscore(k, player_score):
    if k.terminal:
        # Join the arrays of public and private items
        items = player_score.public_items + player_score.private_items
    else:
        # Just public items
        items = player_score.public_items
    total = sum(item.amount for item in items)
    return PublicPlayerScore(
        items=items,
        total=total,
    )


def getprivateplayerscore(s, player_score):
    items = player_score.private_items
    total = sum(item.amount for item in items)
    return PrivatePlayerScore(
        items=items,
        total=total,
    )


@dispatch(State)
def getpublictoplay(k):
    player_idxs = [legal_action.player_idx for legal_action in k.legal_actions]
    # filter out duplicates
    return pvector(list(set(player_idxs)))


@dispatch(State)
def get_max_allotted_times(k):
    return pvector([
        get_player_max_allotted_time(k, player_idx)
        for player_idx in range(k.game_config.num_players)
    ])


@dispatch(State, int)
def get_player_max_allotted_time(k, player_idx):
    max_allotted_seconds = 0
    since_action_idx_of_max = -1
    for legal_action in k.legal_actions:
        if legal_action.player_idx == player_idx:
            if legal_action.allotted_seconds > max_allotted_seconds:
                max_allotted_seconds = legal_action.allotted_seconds
                since_action_idx_of_max = legal_action.allotted_since_action_idx
    if max_allotted_seconds:
        return AllottedTime(
            seconds=max_allotted_seconds,
            since_action_idx=since_action_idx_of_max,
        )
    return None


@dispatch(State, object)
def get_deadline(k, max_allotted_time):
    if not max_allotted_time:
        return None
    since_action_idx = max_allotted_time.since_action_idx
    if since_action_idx == -1:
        allotted_since = datetime.strptime(
            k.game_config.started_at,
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        since_action = k.history[since_action_idx]
        submitted_at = since_action.submitted_at
        allotted_since = datetime.strptime(submitted_at, "%Y-%m-%d %H:%M:%S")
    deadline = allotted_since + timedelta(seconds=max_allotted_time.seconds)
    remaining_seconds = int((deadline - datetime.now()).total_seconds())
    return RemainingAllottedTime(
        seconds=max_allotted_time.seconds,
        remaining_seconds=remaining_seconds,
        since_action_idx=since_action_idx,
    )


@dispatch(State)
def get_deadlines(k):
    if k.terminal:
        return pvector([None for _ in range(k.game_config.num_players)])
    return pvector([
        get_deadline(k, max_allotted_time)
        for max_allotted_time in get_max_allotted_times(k)
    ])


@dispatch(State)
def get_public_player_scores(k):
    return pvector([getpublicplayerscore(k, player.score) for player in k.players])


# deadlines = field(type=list)  # List[RemainingAllottedTime|None]
# game_started_at = field(type=str)
# allotted_times = field(type=list)
# pieces = field(type=list)  # List[Piece]
# to_play = field(type=list)  # List[int]
# bonus_statuses = field(type=list)  # List[BonusStatus]
# starting_piles = field(type=list)  # List[Pile]
# history = field(type=list)  # List[PublicAction]
# player_scores = field(type=list)  # List[PublicPlayerScore]
# goals = field(type=list)  # List[Goal]
# nodes = field(type=list)  # List[Node]
# edges = field(type=list)  # List[Edge]
# regions = field(type=list)
# decks = field(type=list)  # List[PublicDeck]
# piles = field(type=list)  # List[Pile]
# player_idxs = field(type=list)  # List[int]
# players = field(type=list)  # List[PublicPlayer]
# last_to_play = field(type=(int, type(None)), initial=None)
# winners = field(type=list)
# is_terminal = field(type=bool)


# player_score = field(type=PrivatePlayerScore)
# player = field(type=Player)
# goal_completions = field(type=list, initial=v())  # List[GoalCompletion]


@dispatch(PlayerState, object)
def get_candidate_decks(ps: PlayerState, rng: object) -> List[CandidateDeck]:
    candidate_lists = [
        pvector(shuffle_list([c.name for c in public_deck.cards], rng))
        for public_deck in ps.public.deck_statuses
    ]

    note_lists = [
        [f"Deck {deck_idx} started with {len(candidate_deck)} cards"]
        for deck_idx, candidate_deck in enumerate(candidate_lists)
    ]

    for deck_idx, (public_deck, candidates) in enumerate(zip(ps.public.deck_statuses, candidate_lists)):
        # filter out cards that are faceup
        spots_to_remove = [card_name for card_name in public_deck.faceup_spread.spots if card_name]
        for card_name in spots_to_remove:
            if card_name:
                candidates.remove(card_name)

        note_lists[deck_idx].append(f"Removed {len(spots_to_remove)} candidates from deck {public_deck.idx} for faceup spots")
        
        # filter out cards in faceup discard
        for card_name in public_deck.discard_faceup_stack.cards:
            candidates.remove(card_name)

        note_lists[deck_idx].append(f"Removed {len(public_deck.discard_faceup_stack.cards)} candidates from deck {public_deck.idx} for faceup discard")


    # print("ps.private.player.cards: ", len(ps.private.player.cards))
    for card_name in ps.private.player.cards:
        card = getcardfromname(ps, card_name)
        candidate_lists[card.deck_idx].remove(card_name)
        note_lists[card.deck_idx].append(f"Removed 1 candidate from deck {card.deck_idx} for player hand (for player {ps.private.player.idx})")

    return [
        CandidateDeck(
            deck_idx=deck_idx,
            candidates=pvector(candidate_list),
            notes=pvector(note_list + [f"Deck {deck_idx} ends with {len(candidate_list)} cards"])
        )
        for deck_idx, (candidate_list, note_list) in enumerate(zip(candidate_lists, note_lists))
    ]


def imagine_player(p_idx: int, ps: PlayerState, candidate_decks: List[CandidateDeck]) -> Player:
    # print(f"imagine_player {p_idx}")
    if ps.private.player.idx == p_idx:
        # print(f"No need to imagine player {p_idx}, returning private player")
        return ps.private.player
    # print(f"len(candidate_decks[0].candidates): ", len(candidate_decks[0].candidates))
    # print(f"public_player.deck_counts: ", ps.public.players[p_idx].deck_counts)
    public_player = ps.public.players[p_idx]
    # print(f"z1")
    cards = v()
    # print(f"z2")
    for deck_idx, count in enumerate(public_player.deck_counts):
        # print(f"deck_idx: {deck_idx}, count: {count}")
        candidate_deck = candidate_decks[deck_idx]
        # print(f"len(candidate_deck.candidates) before: {len(candidate_deck.candidates)}")
        candidates = candidate_deck.candidates
        for _ in range(count):
            card = candidates[-1]
            candidates = candidates[:-1]
            cards = cards.append(card)
        candidate_decks[deck_idx] = candidate_deck.set(candidates=candidates)
        # print(f"len(candidate_deck.candidates) after: {len(candidate_deck.candidates)}")
    discard_tray = v()
    # print(f"z4")
    for deck_idx, count in enumerate(public_player.discard_deck_counts):
        candidate_deck = candidate_decks[deck_idx]
        candidates = candidate_deck.candidates
        for _ in range(count):
            card = candidates[-1]
            candidates = candidates[:-1]
            discard_tray = discard_tray.append(card)
        candidate_decks[deck_idx] = candidate_deck.set(candidates=candidates)
    return Player(
        idx=p_idx,
        pieces=pvector(public_player.pieces),
        cards=cards,
        discard_tray=discard_tray,
    )


def imagine_players(ps: PlayerState, candidate_decks: List[CandidateDeck]) -> List[Player]:
    imagined = pvector([
        imagine_player(p_idx, ps, candidate_decks)
        for p_idx in range(len(ps.public.players))
    ])
    return imagined


def imagine_decks(ps: PlayerState, candidate_decks: List[CandidateDeck]) -> List[Deck]:
    # print("************************************ candidate_decks[1]: ", candidate_decks[1])
    imagined = pvector([
        imagine_deck(public_deck, candidate_decks[deck_idx])
        for deck_idx, public_deck in enumerate(ps.public.deck_statuses)
    ])
    # print("************************************ imagined[1]: ", imagined[1])
    return imagined


def imagine_deck(public_deck: PublicDeck, candidate_deck: CandidateDeck) -> Deck:
    candidates = candidate_deck.candidates

    # Extract cards for facedown_stack
    num_facedown = public_deck.facedown_stack.num_cards if public_deck.facedown_stack else 0
    facedown_stack_cards = []
    for _ in range(num_facedown):
        facedown_stack_cards.append(candidates[-1])
        candidates = candidates[:-1]
    # print(f"len(facedown_stack_cards) pops for deck_idx [{public_deck.idx}]: ", len(facedown_stack_cards))

    # Extract cards for facedown_spread
    facedown_spread_spots = None
    if public_deck.facedown_spread:
        facedown_spread_spots = []
        for spot in public_deck.facedown_spread.spots:
            if spot:
                facedown_spread_spots.append(candidates[-1])
                candidates = candidates[:-1]
            else:
                facedown_spread_spots.append(None)

    # Extract cards for discard_facedown_stack
    num_discard_facedown = public_deck.discard_facedown_stack.num_cards if public_deck.discard_facedown_stack else 0
    discard_facedown_stack_cards = []
    for _ in range(num_discard_facedown):
        discard_facedown_stack_cards.append(candidates[-1])
        candidates = candidates[:-1]

    imagined = DeckStatus(
        idx=public_deck.idx,
        uuid=public_deck.uuid,
        faceup_stack=(
            public_deck.faceup_stack
            if public_deck.faceup_stack else None
        ),
        faceup_spread=(
            public_deck.faceup_spread
            if public_deck.faceup_spread else None
        ),
        facedown_stack=(
            FacedownCardStack(
                cards=pvector(facedown_stack_cards)
            )
            if public_deck.facedown_stack else None
        ),
        facedown_spread=(
            FacedownCardSpread(
                spots=pvector(facedown_spread_spots)
            )
            if public_deck.facedown_spread and facedown_spread_spots else None
        ),
        discard_faceup_stack=(
            public_deck.discard_faceup_stack
            if public_deck.discard_faceup_stack else None
        ),
        discard_facedown_stack=(
            FacedownCardStack(
                cards=pvector(discard_facedown_stack_cards)
            )
            if public_deck.discard_facedown_stack else None
        ),
    )

    # print("************************************ public_deck.facedown_stack 10: ", public_deck.facedown_stack)
    # print("************************************ imagined.facedown_stack: ", imagined.facedown_stack)

    return imagined


@dispatch(PlayerState, object)
def imagine_state(ps: PlayerState, rng: object) -> State:
    public = ps.public
    public_game_config = ps.game_config

    candidate_decks = get_candidate_decks(ps, rng)

    # print_public_deck_stats(ps.public.deck_statuses[0])
    
    # print("\n")
    # print("************************************ candidate_decks[1].notes a: ", "\n".join(candidate_decks[1].notes))
    # print("************************************ len(candidate_decks[1].candidates) a: ", len(candidate_decks[1].candidates))
    # print("\n")
    
    imagined_decks = imagine_decks(ps, candidate_decks)

    # print("\n")
    # print("************************************ len(candidate_decks[1].candidates) b: ", len(candidate_decks[1].candidates))
    # print("player deck[1] counts: ", [public_player.deck_counts[1] for public_player in ps.public.players])
    # print("\n")

    imagined_players = imagine_players(ps, candidate_decks)
    
    # print("\n")
    # print("************************************ len(candidate_decks[1].candidates) c: ", len(candidate_decks[1].candidates))
    # print("\n")

    imagined_kernel = init_state_kernel(
        getgameconfig(public_game_config),
        public.segment_records,
        piles=public.piles,
        player_idxs=public.player_idxs,
        deck_statuses=imagined_decks,
        players=imagined_players,
        history=pvector(public.history),
    )
    imagined_state = init_memoized_state(imagined_kernel)


    # contains_claim_path_for_p1 = False
    # for action in imagined_state.kernel.history:
    #     if action.legal_action.name == "CLAIM-PATH" and action.legal_action.player_idx == 1:
    #         contains_claim_path_for_p1 = True
    #         break
    
    return imagined_state


@dispatch(State)
def getpublicstate(s):
    return PublicState(
        segment_records=s.segment_records,
        history=s.history,
        game_started_at=s.game_config.started_at,
        piles=s.piles,
        player_idxs=s.player_idxs,
        last_to_play=s.last_to_play,
        bonus_statuses=s.bonus_statuses,
        winners=s.winners,
        terminal=s.terminal,
        deadlines=get_deadlines(s),
        allotted_times=get_max_allotted_times(s),
        to_play=getpublictoplay(s),
        player_scores=get_public_player_scores(s),
        deck_statuses=pvector([getpublicdeck(s, deck) for deck in s.deck_statuses]),
        players=pvector([getpublicplayer(s, p) for p in s.players]),
        nodes=s.nodes,
        edges=s.edges,
    )


@dispatch(State, DeckStatus)
def getpublicdeck(k, d):
    return PublicDeckStatus(
        idx=d.idx,
        uuid=d.uuid,
        faceup_stack = d.faceup_stack if d.faceup_stack else None,
        faceup_spread = d.faceup_spread if d.faceup_spread else None,
        facedown_stack = PublicFacedownCardStack(num_cards=len(d.facedown_stack.cards)) if d.facedown_stack else None,
        facedown_spread = PublicFacedownCardSpread(spots=pvector([spot is not None for spot in d.facedown_spread.spots])) if d.facedown_spread else None,
        discard_faceup_stack = d.discard_faceup_stack if d.discard_faceup_stack else None,
        discard_facedown_stack = PublicFacedownCardStack(num_cards=len(d.discard_facedown_stack.cards)) if d.discard_facedown_stack else None,
    )
    # print("************************************ public_state.deck_statuses[0].facedown_stack 7: ", public_state.deck_statuses[0].facedown_stack)


@dispatch(State, Player)
def getpublicplayer(k, p):
    deck_counts = [0 for _ in k.game_config.fig.board_config.deks]
    for card in p.cards:
        deck_counts[getcardfromname(k, card).deck_idx] += 1
    discard_deck_counts = [0 for _ in k.game_config.fig.board_config.deks]
    for card in p.discard_tray:
        discard_deck_counts[getcardfromname(k, card).deck_idx] += 1
    piece_template_counts = [0 for _ in k.game_config.fig.board_config.piece_templates]
    for piece_name in p.pieces:
        piece_template_counts[getpiecefromname(k, piece_name).piece_template_idx] += 1
    return PublicPlayer(
        idx=p.idx,
        pieces=p.pieces,
        deck_counts=pvector(deck_counts),
        discard_deck_counts=pvector(discard_deck_counts),
        piece_template_counts=pvector(piece_template_counts),
        graph=p.graph,
    )


# Implementing the following Julia function:
# function getplayerpathlens(s::State, player_idx::Int)
#     getpathlens(s)[getplayerpathidxs(s, player_idx)]
# end
def getplayerpathlens(s, player_idx):
    path_lens = getpathlens(s)
    player_path_idxs = getplayerpathidxs(s, player_idx)
    return [path_lens[idx] for idx in player_path_idxs]


# Implementing the following Julia function:
# getpathlens(s::State) = length.(getfield.(getfield.(s.fig.board_config.board_paths, :path), :segments))
def getpathlens(s):
    return [len(p.path.segments) for p in s.game_config.fig.board_config.board_paths]

# Implementing the following Julia function:
# function getplayerpathidxs(s::State, player_idx::Int)
#     s.player_hands[player_idx].paths
# end
def getplayerpathidxs(s, player_idx):
    return s.player_hands[player_idx].paths


# Function implements the following Julia function:
# function getlastactionkey(s)
#     last_action = getlastaction(s)
#     if isnothing(last_action)
#         return nothing
#     end
#     Val(Symbol(last_action.action_name))
# end
@dispatch(State)
def getlastactiontype(s):
    pass


def getactiontype(action_name):
    match action_name:
        case "ROUTE_DISCARD":
            return RouteDiscardAction()
        case "DRAW_UNIT_DECK":
            return DrawUnitDeckAction()
        case "DRAW_UNIT_FACEUP":
            return DrawUnitFaceupAction()
        case "CLAIM_POINT":
            return ClaimPointAction()
        case "CLAIM_PATH":
            return MovePiecesToPathAction()
    
    return NoAction()


# Function implements the following Julia function:
# getlastplayeridxplus1(s) = mod1(getlastaction(s).player_idx + 1, s.kernel.game_config.num_players)
def getlastplayeridxplus1(s):
    pass


@dispatch(State)
def gettoplay(s):
    return gettoplay(s, getlastactiontype(s))


@dispatch(State, object)
def gettoplay(s, last_action_type):
    return [getlastplayeridxplus1(s)]


def getrng(seed):
    rng = random.Random()
    rng.seed(seed)
    return rng


# Implementing the following Julia function:
# getfirstplayeridx(g::Game) = rand(getrng(g), 1:g.num_players)
def getfirstplayeridx(rng, num_players):
    return rng.randint(0, num_players-1)


@dispatch(State, int)
def get_legal_actions3(s, player_idx):
    return pvector([a for a in s.legal_actions if a.player_idx == player_idx])


@dispatch(State, int)
def get_legal_actions(s, player_idx):
    return [a for a in s.legal_actions if a.player_idx == player_idx]


@dispatch(State, int)
def get_goal_completions(kernel, player_idx):
    return pvector([
        GoalCompletion(
            goal_idx=goal.idx,
            goal_uuid=goal.uuid,
            complete=is_goal_complete(kernel, goal, player_idx),
        )
        for goal in get_goals(kernel, player_idx)
    ])


# @dispatch(State, FrozenGoal, int)
def is_goal_complete(kernel, goal, player_idx, log=False):
    # TODO: fix!, this should be memoized
    neighbors = kernel.players[player_idx].graph.neighbors
    # neighbors = calc_player_graph3(
    #     kernel.game_config,
    #     kernel.segment_records,
    #     player_idx,
    # ).neighbors

    node_idxs = [kernel.game_config.fig.nodeuuid2idx[node_uuid] for node_uuid in goal.node_uuids]
    # if log:
    #     print("\n\n")
    #     print("(is_goal_complete) neighbors: ", [list(x) for x in neighbors])
    #     print(f"(is_goal_complete) are_nodes_connected({node_idxs}): ", are_nodes_connected([list(x) for x in neighbors], node_idxs, True))
    return are_nodes_connected(
        neighbors,
        node_idxs,
        log,
    )


def are_nodes_connected(neighbors, node_set, log=False):
    if len(node_set) == 0:
        raise ValueError("Node set cannot be empty")
    if len(node_set) <= 1:
        return True  # Trivial cases
    
    node_set = set(node_set)  # For faster lookups
    start = next(iter(node_set))  # Pick any starting node
    
    visited = set()
    queue = deque([start])
    visited.add(start)
    
    while queue:
        current = queue.popleft()
        for neighbor in neighbors[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    # print("type(node_set[0]): ", type(next(iter(node_set))))
    # Check if all nodes in the set were visited
    if log:
        print(f"(are_nodes_connected) neighbors: {neighbors}")
        print(f"(are_nodes_connected) node_set: {node_set}")
        print(f"(are_nodes_connected) all(node in visited for node in node_set): {all(node in visited for node in node_set)}")
        # for node in node_set:
        #     print(f"node({node}) in visited({visited}): {node in visited}")

    return all(node in visited for node in node_set)


@dispatch(State, int)
def get_goals(kernel, player_idx):
    fig = kernel.game_config.fig
    player = kernel.players[player_idx]
    goal_uuids = [getcardfromname(kernel, card_name).goal_uuid for card_name in player.cards if getcardfromname(kernel, card_name).goal_uuid]
    return [
        fig.goals[fig.goaluuid2idx[goal_uuid]] 
        for goal_uuid in goal_uuids
    ]


def getrepeatplayerbooltype(s, player_idx):
    pass


def combinations(a, n=None):
    if n is None:
        return chain.from_iterable(itertools_combinations(a, r) for r in range(len(a) + 1))
    return itertools_combinations(a, n)


# def combinations(a, n=None):
#     """
#     Generate combinations from a sequence a.

#     If n is specified, generate all combinations of n elements from a.
#     If n is not specified, generate combinations of all sizes, from 0 to len(a).

#     The function returns an iterator. To collect all combinations into a list,
#     use list(combinations(a, n)).

#     Note: a should be a sequence with a defined length, such as a list or tuple.
#     """
#     if n is None:
#         return itertools.chain.from_iterable(itertools.combinations(a, k) for k in range(len(a)+1))
#     else:
#         return itertools.combinations(a, n)


###
# Causal function chain is:
# gettoplay => getlegalactions => isterminal
#
# So, gettoplay() determines getlegalactions().
# Moreover, if there are no "legal_actions" for "to_play",
# then the state is "terminal".
###


# Implementing the following Julia function:
# function getpotentialpathnums(s::State, player_num::Int)
#     num_pieces = s.player_hands[player_num].num_pieces
#     setdiff(
#         Set(getpathidxs(s.fig, num_pieces)),
#         Set(getunavailablepaths(s, player_num)),
#     ) |> collect
# end
def getpotentialpathidxs(s, player_num):
    num_pieces = s.player_hands[player_num-1].num_pieces
    return list(
        set(getpathidxs(s.game_config.fig, num_pieces)) - set(getunavailablepathidxs(s, player_num))
    )
    # return list(set(getpathidxs(s.fig, num_pieces)) - set(getunavailablepaths(s, player_num)))


# Implementing the following Julia function:
# function getpathidxs(f::Fig, max_pieces::Int)
#     [p.num for p in f.board_config.board_paths if length(p.path.segments) <= max_pieces]
# end
def getpathidxs(fig, max_pieces):
    return [
        (p.num - 1)
        for p in fig.board_config.board_paths
        if len(p.path.segments) <= max_pieces
    ]


# Implementing the following Julia function:
# function getunavailablepaths(s::State, player_idx::Int)
#     link2paths = Dict()
#     path2link = Dict()

#     for board_path in s.fig.board_config.board_paths
#         (; link_num) = board_path
#         if !haskey(link2paths, link_num)
#             link2paths[link_num] = []
#         end
#         push!(link2paths[link_num], board_path.num)
#         path2link[board_path.num] = link_num
#     end

#     multipath_links = [board_link.num for board_link in getmultipathlinks(s.fig)]

#     # TODO: this is fig-specific game logic 
#     # and should be factored out.
#     if s.game.num_players < 4
#         blocking_hands = s.player_hands
#     else
#         blocking_hands = [s.player_hands[player_idx]]
#     end

#     unavailable_links = v()
#     for hand in blocking_hands
#         for path_idx in hand.paths
#             link_idx = path2link[path_idx]
#             if in(link_idx, multipath_links)
#                 push!(unavailable_links, link_idx)
#             end
#         end
#     end

#     unavailable_paths = getclaimedpathidxs(s)
#     for link_idx in unavailable_links
#         for peer in link2paths[link_idx]
#             push!(unavailable_paths, peer)
#         end
#     end

#     unavailable_paths |> unique
# end
def getunavailablepathidxs(s, player_idx):
    link2paths = {}
    path2link = {}

    for board_path in s.game_config.fig.board_config.board_paths:
        link_idx = board_path.link_num - 1
        if link_idx not in link2paths:
            link2paths[link_idx] = []
        link2paths[link_idx].append(board_path.num-1)
        path2link[board_path.num-1] = link_idx

    multipath_links = [(board_link.num-1) for board_link in getmultipathlinks(s.game_config.fig)]

    if s.game_config.num_players < 4:
        blocking_hands = s.player_hands
    else:
        blocking_hands = [s.player_hands[player_idx]]

    unavailable_links = v()
    for hand in blocking_hands:
        for path_idx in hand.paths:
            link_idx = path2link[path_idx]
            if link_idx in multipath_links:
                unavailable_links = unavailable_links.append(link_idx)

    unavailable_paths = getclaimedpathidxs(s)
    for link_idx in unavailable_links:
        unavailable_paths = unavailable_paths.extend(link2paths[link_idx])

    return list(set(unavailable_paths))


# Implementing the following Julia function:
# function getmultipathlinks(f::Fig)
#     filter(
#         frozen_link->frozen_link.width > 1,
#         f.board_config.links,
#     )
# end
def getmultipathlinks(fig):
    return [
        frozen_link
        for frozen_link in fig.board_config.links
        if frozen_link.width > 1
    ]


# Implementing the following Julia function:
# function prioritysort(fig::Fig, segments::Vector)
#     (; board_config) = fig
#     (; deck_units) = board_config
#     unituuid2deckunit = Dict(x.unit_uuid => x for x in deck_units)
#     to_sort = [OrderedSegment(n, segment) for (n, segment) in enumerate(segments)]
#     function lt(a, b)
#         segment_a = a.segment
#         segment_b = b.segment
#         deck_unit_a = isnothing(segment_a.unit_uuid) ? nothing : unituuid2deckunit[segment_a.unit_uuid]
#         deck_unit_b = isnothing(segment_b.unit_uuid) ? nothing : unituuid2deckunit[segment_b.unit_uuid]
#         if isnothing(deck_unit_a) && isnothing(deck_unit_b)
#             return a.path_segment_num < b.path_segment_num
#         elseif isnothing(deck_unit_a) && !isnothing(deck_unit_b)
#             return true
#         elseif !isnothing(deck_unit_a) && isnothing(deck_unit_b)
#             return false
#         elseif deck_unit_a.is_wild && deck_unit_b.is_wild
#             return a.path_segment_num < b.path_segment_num
#         elseif deck_unit_a.is_wild && !deck_unit_b.is_wild
#             return false
#         elseif !deck_unit_a.is_wild && deck_unit_b.is_wild
#             return true
#         end
#         a.path_segment_num < b.path_segment_num
#     end
#     Base.sort(to_sort; lt=lt, rev=true)
# end
def prioritysort(fig, segments):
    board_config = fig.board_config
    deck_units = board_config.deck_units
    unituuid2deckunit = {x.unit_uuid: x for x in deck_units}
    to_sort = [OrderedSegment(path_segment_num=n, segment=segment) for n, segment in enumerate(segments)]
    
    def lt(a, b):
        segment_a = a.segment
        segment_b = b.segment
        deck_unit_a = unituuid2deckunit.get(segment_a.unit_uuid) if segment_a.unit_uuid else None
        deck_unit_b = unituuid2deckunit.get(segment_b.unit_uuid) if segment_b.unit_uuid else None
        
        if deck_unit_a is None and deck_unit_b is None:
            return a.path_segment_num < b.path_segment_num
        elif deck_unit_a is None and deck_unit_b is not None:
            return True
        elif deck_unit_a is not None and deck_unit_b is None:
            return False
        elif deck_unit_a.is_wild and deck_unit_b.is_wild:
            return a.path_segment_num < b.path_segment_num
        elif deck_unit_a.is_wild and not deck_unit_b.is_wild:
            return False
        elif not deck_unit_a.is_wild and deck_unit_b.is_wild:
            return True
        
        return a.path_segment_num < b.path_segment_num
    
    return sorted(to_sort, key=cmp_to_key(lt), reverse=True)


# Implementing the following Julia function:
# getwildunituuids(f::Fig) = [x.unit_uuid for x in f.board_config.deck_units if x.is_wild]
def getwildunituuids(fig):
    return [x.unit_uuid for x in fig.board_config.deck_units if x.is_wild]

# Implementing the following Julia function:
# getnonwildunituuids(f::Fig) = [x.unit_uuid for x in f.board_config.deck_units if !x.is_wild]
def getnonwildunituuids(fig):
    return [x.unit_uuid for x in fig.board_config.deck_units if not x.is_wild]


# Implementing the following Julia function:
# function getunituuid(f::Fig, card_num::Int)
#     from = 1
#     for deck_unit in f.board_config.deck_units
#         (; quantity, unit_uuid) = deck_unit
#         to = from + quantity - 1
#         if from <= card_num <= to
#             return unit_uuid
#         end
#         from += quantity
#     end
#     throw(ErrorException("unit_uuid not found for card_num $card_num"))
# end
def getunituuid(fig, card_num):
    from_idx = 1
    for deck_unit in fig.board_config.deck_units:
        quantity = deck_unit.quantity
        unit_uuid = deck_unit.unit_uuid
        to = from_idx + quantity - 1
        if from_idx <= card_num <= to:
            return unit_uuid
        from_idx += quantity
    raise ValueError(f"unit_uuid not found for card_num {card_num}")


# Implementing the following Julia function:
# function getclaimedpathidxs(s::State)
#     claimed = v()
#     for player_hand in s.player_hands
#         append!(claimed, player_hand.paths)
#     end
#     claimed
# end
def getclaimedpathidxs(s):
    claimed = v()
    for player_hand in s.player_hands:
        claimed = claimed.extend(player_hand.paths)
    return claimed






# Implementing the following Julia function:
# function getnodeuuids(f::Fig, remaining_pieces::Int)
#     point_capture_unit_count = getsettingvalue(f, :point_capture_unit_count)
#     if point_capture_unit_count <= remaining_pieces
#         return [p.uuid for p in f.board_config.points]
#     end
#     []
# end
def getnodeuuids(f, remaining_pieces):
    point_capture_unit_count = getsettingvalue(f, 'point_capture_unit_count')
    # print(f"f.board_config: ", f.board_config)
    # print(f"f.board_config: ", f.board_config.points)
    if point_capture_unit_count <= remaining_pieces:
        return [p.uuid for p in f.board_config.points]
    return v()


# Implementing the following Julia function:
# function getunavailablepoints(s::State)
#     unavailable_points = v()
#     for hand in s.player_hands
#         for point_uuid in hand.points
#             push!(unavailable_points, point_uuid)
#         end
#     end
#     unavailable_points
# end
def getunavailablepoints(s):
    unavailable_points = v()
    for hand in s.player_hands:
        for point_uuid in hand.points:
            unavailable_points = unavailable_points.append(point_uuid)
    return unavailable_points


def printplayer(s, player_idx):
    pass


def printstate(s):
    pass


def printaction(a, i):
    pass


# Implementing the following Julia function:
# getprivatescore(s::State, player_idx::Int; bonus=true) = getprivatescore(s, s.player_hands[player_idx]; bonus=bonus)
# Note: Updated to work with State instead of State
@dispatch(State, int)
def getprivatescore(s, player_idx):
    player_score_obj = getprivateplayerscore(s, s.players[player_idx].score)
    return (player_score_obj.total, player_score_obj)


# Implementing the following Julia function:
# function getscorecodeidx(f::Fig, score_code::Symbol)
#     findfirst(
#         isequal(string(score_code)),
#         getscorecodes(f),
#     )
# end
def getscorecodeidx(f, score_code):
    return getscorecodes(f).index(score_code)


# Implementing the following Julia function:
# function getscorecodes(f::Fig)
#     score_codes = ["PATH", "ROUTE", "CLUSTER"]
#     disable_longest_path_bonus = getsettingvalue(f, :disable_longest_path_bonus)
#     if !disable_longest_path_bonus
#         push!(score_codes, "LONGEST_ROAD", "MOST_CLUSTERS")
#     end
#     score_codes
# end
# # TODO: this list needs to be remove, totally unnecessary.
def getscorecodes(f):
    score_codes = ["PATH", "ROUTE", "CLUSTER"]
    disable_longest_path_bonus = getsettingvalue(f, 'disable_longest_path_bonus')
    if not disable_longest_path_bonus:
        score_codes.extend(["LONGEST_ROAD", "MOST_CLUSTERS"])
    return score_codes


def getvalidspotnums(s):
    return [n for n in range(1, len(s.faceup_spread.spots) + 1) if s.faceup_spread.spots[n-1] is not None]


def json_serializer(obj):
    if isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, '__todict__'):
        return obj.__todict__()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@dispatch(str, str, Fig, int, int)
def initgameconfig(uuid, started_at, fig, num_players, seed):
    starting_decks = v()

    for dek in fig.board_config.deks:
        cards = generate_cards(dek, fig.resourceuuid2idx, fig.goaluuid2idx)
        deck_obj = Deck(
            uuid=dek.uuid,
            idx=dek.idx,
            cards=cards,
        )
        starting_decks = starting_decks.append(deck_obj)

    starting_piles = v()
    for piece_template in fig.board_config.piece_templates:
        if piece_template.has_player:
            for player_idx in range(num_players):
                pile_idx=len(starting_piles)
                pieces = generate_pieces(piece_template, pile_idx, player_idx)
                pile = Pile( 
                    idx=pile_idx,
                    player_idx=player_idx,
                    num_pieces=piece_template.quantity,
                    pieces=pieces,
                )
                starting_piles = starting_piles.append(pile)

    return GameConfig(
        uuid=uuid,
        started_at=started_at,
        fig=fig,
        num_players=num_players,
        seed=seed,
        starting_decks=starting_decks,
        starting_piles=starting_piles,
        wild_unit_uuids=get_wild_unit_uuids(starting_decks),
    )


def rng2json(rng):
    """Convert a random.Random instance to a JSON string."""
    rng_state = rng.getstate()
    return json.dumps({"state": [rng_state[0], list(rng_state[1]), rng_state[2]]})


def json2rng(json_str):
    """Reconstruct a random.Random instance from a JSON string."""
    data = json.loads(json_str)
    state_data = data["state"]
    
    # Create a new Random instance
    rng = random.Random()
    
    # Convert the middle part back to tuple of integers
    state = (state_data[0], tuple(state_data[1]), state_data[2])
    
    # Set the state
    rng.setstate(state)
    
    return rng


# Implementing the following Julia function:
# function getprivatestate(s::State, player_idx::Int)
#     legal_actions = getlegalactions(s, player_idx)
#     PrivateState(
#         getpublicstate(s),
#         legal_actions,
#         getsegmentstatuses(s, player_idx),
#         s.player_hands[player_idx],
#     )
# end
@dispatch(State, int)
def getprivatestate(s, player_idx):
    return PrivateState(
        my_history=pvector([a for a in s.history if a.legal_action.player_idx == player_idx]),
        player_score=getprivateplayerscore(s, s.players[player_idx].score),
        player=s.players[player_idx],
        legal_actions = get_legal_actions3(s, player_idx),
        goal_completions=get_goal_completions(s, player_idx),
    )


# Implement the following Julia function
# function getqvaluetrajectories(g::Game)
#     curr_state = getinitialstate(g)
#     states = State[]
#     scores = [Int[] for _ in 1:(length(g.actions)+1)]
#     action_player_nums = Vector{Int}(undef, length(g.actions)) 
#     q_values = Vector{Int}(undef, length(g.actions))
#     formula_q_idxs = Vector{Union{Nothing,Int}}(nothing, length(g.actions))
#     formula_score_diffs = Vector{Tuple{Int,Int}}(undef, length(g.actions))
#     for (i,action) in enumerate(g.actions)
#         push!(states, curr_state)
#         scores[i] = map(1:g.num_players) do player_num
#             getprivatescore(curr_state, player_num; bonus=true).total
#         end
#         action_player_nums[i] = action.player_idx
#         curr_state = getnextstate(curr_state, action)
#     end
#     scores[end] = map(1:g.num_players) do player_num
#         getprivatescore(curr_state, player_num; bonus=true).total
#     end
#     for player_num in 1:g.num_players
#         player_action_idxs = findall(isequal(player_num), action_player_nums)
#         player_action_idxs_plus_terminal_idx = [player_action_idxs..., length(scores)]
#         scores_at_player_action_idxs = [x[player_num] for x in scores[player_action_idxs_plus_terminal_idx]]
#         q_values_at_player_action_idxs = reverse(cumsum(-diff(reverse(scores_at_player_action_idxs))))
#         q_values[player_action_idxs] = q_values_at_player_action_idxs
#         formula_q_idxs[player_action_idxs[1:end-1]] .= player_action_idxs[2:end]
#         formula_score_diffs[player_action_idxs] .= map(enumerate(player_action_idxs_plus_terminal_idx[1:end-1])) do (i,idx)
#             (player_action_idxs_plus_terminal_idx[i+1], idx)
#         end
#     end
#     formulas = map(zip(formula_q_idxs, formula_score_diffs)) do (formula_q_idx, formula_score_diff)
#         QValueFormula((q_num=formula_q_idx, score_diff=formula_score_diff))
#     end
#     QValueTrajectories(scores, q_values, formulas, states, g.actions)
#     # for player_idx in 1:g.num_players
#     # end
#     # -diff([110,10,0,0])
#     # cumsum([100,10,0])
# end
@dispatch(GameConfig, list)
def get_qvalue_trajectories(game_config, actions):
    curr_state = getinitialstate(game_config)
    states = v()
    scores = np.array([list([0] * game_config.num_players) for _ in range(len(actions) + 1)])
    action_player_idxs = [None] * len(actions)
    q_values = [None] * len(actions)
    formula_q_idxs = np.array([None] * len(actions))
    formula_score_diffs = np.array([None] * len(actions))

    for i, action in enumerate(actions):
        states = states.append(curr_state)
        scores[i] = list([getprivatescore(curr_state, player_idx)[0] for player_idx in range(game_config.num_players)])
        action_player_idxs[i] = action.player_idx
        curr_state = getnextstate(curr_state, action)

    scores[-1] = np.array([getprivatescore(curr_state, player_idx)[0] for player_idx in range(game_config.num_players)])

    for player_idx in range(game_config.num_players):
        player_action_idxs = [i for i, x in enumerate(action_player_idxs) if x == player_idx]

        player_action_idxs_plus_terminal_idx = player_action_idxs + [len(scores) - 1]
        scores_at_player_action_idxs = [x[player_idx] for x in scores[player_action_idxs_plus_terminal_idx]]
        q_values_at_player_action_idxs = np.flip(
            np.cumsum((-1 * np.diff(np.flip(np.array(scores_at_player_action_idxs)))))
        )

        for idx, action_idx in enumerate(player_action_idxs):
            q_values[action_idx] = q_values_at_player_action_idxs[idx].item()

        formula_q_idxs[player_action_idxs[:-1]] = player_action_idxs[1:]

        formula_score_diffs[player_action_idxs] = [
            (player_action_idxs_plus_terminal_idx[i+1], idx)
            for i, idx in enumerate(player_action_idxs_plus_terminal_idx[:-1])
        ]

    formulas = [
        QValueFormula(q_num=formula_q_idx, score_diff=ScoreDiff(a=formula_score_diff[0], b=formula_score_diff[1]))
        for formula_q_idx, formula_score_diff in zip(formula_q_idxs, formula_score_diffs)
    ]

    return QValueTrajectories(scores=scores.tolist(), q_values=q_values, formulas=formulas, states_no_terminal=states, actions=actions)


@dispatch(str, str, str, int, int, list)
def get_qvalue_trajectories(logged_game_uuid, started_at, static_board_config_uuid, board_config_json, num_players, seed, actions):
    game_config = initgameconfig(logged_game_uuid, started_at, static_board_config_uuid, board_config_json, num_players, seed)
    return get_qvalue_trajectories(game_config, actions)


@dispatch(str, str, str, int, int)
def initgameconfig(logged_game_uuid, started_at, static_board_config_uuid, board_config_json, num_players, seed):
    board_config = FrozenBoardConfig.__fromdict__(json.loads(board_config_json))
    return initgameconfig(
        logged_game_uuid, 
        started_at,
        initfig(static_board_config_uuid, board_config),
        num_players, 
        seed,
    )


# Implementing the following Julia function:
# diff(A::AbstractVector)
# diff(A::AbstractArray; dims::Integer)

#   Finite difference operator on a vector or a multidimensional array A. In the latter case the dimension to operate on needs to be specified with the dims keyword argument.

#   │ Julia 1.1
#   │
#   │  diff for arrays with dimension higher than 2 requires at least Julia 1.1.

#   Examples
#   ≡≡≡≡≡≡≡≡

#   julia> a = [2 4; 6 16]
#   2×2 Matrix{Int64}:
#    2   4
#    6  16
  
#   julia> diff(a, dims=2)
#   2×1 Matrix{Int64}:
#     2
#    10
  
#   julia> diff(vec(a))
#   3-element Vector{Int64}:
#     4
#    -2
#    12
def diff(A, dims=None):
    if dims is None:
        # For 1D arrays, return the difference between consecutive elements
        return [A[i] - A[i - 1] for i in range(1, len(A))]
    else:
        # For 2D arrays, compute the difference along the specified dimension
        if dims == 1:
            return [[A[i][j] - A[i - 1][j] for j in range(len(A[0]))] for i in range(1, len(A))]
        elif dims == 2:
            return [[A[i][j] - A[i][j - 1] for j in range(1, len(A[0]))] for i in range(len(A))]
        else:
            raise ValueError("dims must be either 1 or 2")


def get_default_toplay(s):
    if s.legal_actions:
        return s.legal_actions[0].player_idx
    return None


def get_toplay(s):
    return list(
        set(legal_action.player_idx for legal_action in s.legal_actions)
    )


@dispatch(PrivateState, object)
def get_intuited_best_actions1(private_state: PrivateState, rng: object):
    possible_actions = [
        legal_action.get_default_action()
        for legal_action in private_state.legal_actions
    ]
    if not possible_actions:
        return None
    # return possible_actions[-1:]
    return possible_actions[:5]


@dispatch(PlayerState, object)
def get_intuited_best_actions(ps: PlayerState, rng: object):
    imagined_state = imagine_state(ps, rng)
    possible_actions = [
        legal_action.get_default_action(imagined_state)
        for legal_action in ps.private.legal_actions
    ]
    if not possible_actions:
        return None
    # return possible_actions[-1:]
    return possible_actions[:64]


def get_spread(q_values, p_idx):
    my_q = q_values[p_idx]
    other_qs = [q for i, q in enumerate(q_values) if i != p_idx]
    spread = my_q - max(other_qs)
    return spread


def getvproxy0(ps):
    return 0


@dispatch(PlayerState, Action2, object)
def imagine_dynamics(ps: PlayerState, a: Action2, rng: object):
    return dynamics(imagine_state(ps, rng), a)


@dispatch(State, Action2)
def dynamics(s, a):
    totals = [score.total for score in get_public_player_scores(s)]

    next_s = getnextstate2(s, a)
    next_totals = [score.total for score in get_public_player_scores(next_s)]

    # print(f"len(history): {len(s.history)} (last: {s.history[-1].legal_action.name} by p{s.history[-1].legal_action.player_idx}) totals: ", totals, " next_totals: ", next_totals)
    # print("\n")

    rewards = [next_total - total for (total, next_total) in zip(totals, next_totals)]
    return next_s, rewards


def alpha0(ps: PlayerState, rng: object, td=3):
    # print("************************************ ps.public.deck_statuses[0].facedown_stack 8: ", ps.public.deck_statuses[0].facedown_stack)
    legal_actions = ps.private.legal_actions
    if not legal_actions:
        return None
    intuited = get_intuited_best_actions(ps, rng)
    q_proxies = [getqproxy0(ps, a, td, rng) for a in intuited]
    max_spread_idx = get_max_spread_idx(q_proxies, ps.private.player.player_idx)
    return intuited[max_spread_idx]


def get_max_spread_idx(q_proxies, p_idx):
    if len(q_proxies) == 0:
        raise ValueError("q_proxies cannot be empty")
    if len(q_proxies) == 1:
        return 0
    spreads = [get_spread(q_proxy, p_idx) for q_proxy in q_proxies]
    max_spread_idx = np.argmax(spreads)
    return max_spread_idx


@dispatch(State, Action2, int, object)
def getqproxy1(imagined_state: State, a: Action2, td: int, rng: object):
    next_s, rewards = dynamics(imagined_state, a)

    if next_s.terminal:
        return rewards

    if td == 0:
        v_proxies = [
            0 for _ in range(next_s.game_config.num_players)
        ]
        q_values = [r + v for (r, v) in zip(rewards, v_proxies)]
        return q_values

    next_p_idx = get_default_toplay(next_s)
    next_private_state = getprivatestate(next_s, next_p_idx)
    next_intuited_actions = get_intuited_best_actions1(next_private_state, rng)
    next_player_state = PlayerState(
        game_config=getpublicgameconfig(next_s.game_config),
        public=getpublicstate(next_s),
        private=next_private_state,
    )
    next_imagined_state = imagine_state(next_player_state, rng)
    competing_next_q_values = [getqproxy1(next_imagined_state, a, td-1, rng) for a in next_intuited_actions]
    max_next_spread_idx = get_max_spread_idx(competing_next_q_values, next_p_idx)
    next_q_values = competing_next_q_values[max_next_spread_idx]
    q_values = [r + next_q_values[i] for i, r in enumerate(rewards)]
    return q_values


@dispatch(PlayerState, Action2, int, object)
def getqproxy0(ps: PlayerState, a: Action2, td: int, rng: object):
    # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ getqproxy0 td: ", td)

    def qproxybase(ps, a, rng):
        next_s, rewards = imagine_dynamics(ps, a, rng)
        if next_s.terminal:
            return rewards
        v_proxies = [
            getvproxy0(getprivatestate(next_s, i))
            for i in range(next_s.game_config.num_players)
        ]
        q_proxies = [
            r + v_proxies[i]
            for i, r in enumerate(rewards)
        ]
        return q_proxies

    def qproxyrecurse(ps, a, rng):
        next_s, rewards = imagine_dynamics(ps, a, rng)
        if next_s.terminal:
            return rewards
        next_p_idx = get_default_toplay(next_s)
        next_ps = getprivatestate(next_s, next_p_idx)
        player_state = PlayerState(
            game_config=getpublicgameconfig(next_s.game_config),
            public=getpublicstate(next_s),
            private=next_ps,
        )
        next_intuited = get_intuited_best_actions(player_state, rng)
        competing_next_q_values = [getqproxy0(player_state, a, td-1, rng) for a in next_intuited]
        max_next_spread_idx = get_max_spread_idx(competing_next_q_values, next_p_idx)
        next_q_values = competing_next_q_values[max_next_spread_idx]
        q_values = [r + next_q_values[i] for i, r in enumerate(rewards)]
        return q_values

    return qproxyrecurse(ps, a, rng) if td > 0 else qproxybase(ps, a, rng)


INIT_HOOK_1 = """def handler(kernel):
    return shuffle_all_decks(kernel)  
"""
INIT_HOOK_2 = """def handler(kernel):
    return deal_cards_to_each_player(kernel, 0, 4)
"""
INIT_HOOK_3 = """def handler(kernel):
    return deal_cards_to_each_player_discard_tray(kernel, 1, 3)
"""
INIT_HOOK_4 = """def handler(kernel):
    return distribute_all_piles(kernel)
"""
INIT_HOOK_5 = """def handler(kernel):
    return flip_cards(kernel, 0, 5)
"""
INIT_HOOK_7 = """def handler(kernel):
    return shuffle_player_order(kernel)
"""

INITIALIZATION_HOOKS = [
    Hook(
        name="SampleHook1",
        uuid="81248263-5cb4-4439-afea-78c01aba3de3",
        when="AFTER_GAME_STARTS",
        code=INIT_HOOK_1,
    ),
    Hook(
        name="SampleHook2",
        uuid="d654d7f6-c2f4-443d-b603-8fa034717830",
        when="AFTER_GAME_STARTS",
        code=INIT_HOOK_2,
    ),
    Hook(
        name="SampleHook3",
        uuid="ffbc3d4a-85c6-461d-9272-0ddeb873f216",
        when="AFTER_GAME_STARTS",
        code=INIT_HOOK_3,
    ),
    Hook(
        name="SampleHook4",
        uuid="e3a9161b-ad27-4166-a013-77ebcd2f75b7",
        when="AFTER_GAME_STARTS",
        code=INIT_HOOK_4,
    ),
    Hook(
        name="SampleHook5",
        uuid="bff1a9e9-90a5-4431-9d41-2b68c5eff55e",
        when="AFTER_GAME_STARTS",
        code=INIT_HOOK_5,
    ),
    Hook(
        name="SampleHook7",
        uuid="240b8706-7fcf-4d35-9894-276aa10f799f",
        when="AFTER_GAME_STARTS",
        code=INIT_HOOK_7,
    ),
]


HANDLE_ACTION_HOOK_1 = """
def handler(kernel, action):
    return default_handle_action(kernel, action)
"""

HANDLE_ACTION_HOOKS = [
    Hook(
        name="SampleHookHandleAction1",
        uuid="11e83980-5a10-43f0-9504-66fe66eebb11",
        when="HANDLE_ACTION",
        code=HANDLE_ACTION_HOOK_1,
    ),
]

AFTER_ACCEPT_ACTION_HOOK_1 = """
def handler(kernel, action):
    return default_after_accept_action(kernel, action)
"""

AFTER_ACCEPT_ACTION_HOOKS = [
    Hook(
        name="SampleHookAfterAcceptAction1",
        uuid="3467e35e-f6b6-4b75-aeff-97e4bab47c75",
        when="AFTER_ACCEPT_ACTION",
        code=AFTER_ACCEPT_ACTION_HOOK_1,
    )
]

ACCEPT_ACTION_HOOK_1 = """
def handler(game, action):
    return default_accept_action(game, action)
"""

ACCEPT_ACTION_HOOKS = [
    Hook(
        name="SampleHookAcceptAction1",
        uuid="01b8ce2c-9aa5-44f5-b82f-bc22afeb49ef",
        when="ACCEPT_ACTION",
        code=ACCEPT_ACTION_HOOK_1,
    )
]

HANDLE_SCORING_HOOK_1 = """
def handler(game):
    return default_handle_scoring(game)
"""

HANDLE_SCORING_HOOKS = [
    Hook(
        name="SampleHookHandleScoring1",
        uuid="11e83980-5a10-43f0-9504-66fe66eebb11",
        when="HANDLE_SCORING",
        code=HANDLE_SCORING_HOOK_1,
    ),
]

HANDLE_TERMINAL_HOOK_1 = """
def handler(game):
    return default_handle_terminal(game)
"""

HANDLE_TERMINAL_HOOKS = [
    Hook(
        name="SampleHookHandleTerminal1",
        uuid="11e83980-5a10-43f0-9504-66fe66eebb11",
        when="HANDLE_TERMINAL",
        code=HANDLE_TERMINAL_HOOK_1,
    ),
]

@dispatch(State, int)
def get_default_legal_actions(state_kernel, player_idx):
    allotted_seconds = DEFAULT_ALLOTTED_SECONDS
    allotted_since_action_idx = len(state_kernel.history) - 1
    legal_actions = v()

    if len(state_kernel.deck_statuses[1].facedown_stack.cards) >= 1:
        legal_actions = legal_actions.append(
            init_legal_action(
                player_idx=player_idx,
                name="DRAW-GOAL-CARDS",
                instruction="draw a route",
                allotted_seconds=allotted_seconds,
                allotted_since_action_idx=allotted_since_action_idx,
                draw_discard=LegalActionDrawDiscard(
                    deck_idx=1,
                    quantity=3,
                    min=1,
                )
            )
        )

    if len(state_kernel.deck_statuses[0].facedown_stack.cards) >= 1:
        legal_actions = legal_actions.append(
            init_legal_action(
                auto_preferred=True,
                player_idx=player_idx,
                name="BLIND-DRAW-RESOURCE-CARD",
                instruction="draw a unit",
                allotted_seconds=allotted_seconds,
                allotted_since_action_idx=allotted_since_action_idx,
                draw=LegalActionDraw(
                    deck_idx=0,
                    quantity=1,
                )
            )
        )

    if len(state_kernel.deck_statuses[0].facedown_stack.cards) >= 2:
        legal_actions = legal_actions.append(
            init_legal_action(
                player_idx=player_idx,
                name="BLIND-DRAW-TWO-RESOURCE-CARDS",
                instruction="draw 2 units",
                allotted_seconds=allotted_seconds,
                allotted_since_action_idx=allotted_since_action_idx,
                draw=LegalActionDraw(
                    deck_idx=0,
                    quantity=2,
                )
            )
        )

    for card_name in state_kernel.deck_statuses[0].faceup_spread.spots:
        if card_name:
            legal_actions = legal_actions.append(
                init_legal_action(
                    player_idx=player_idx,
                    name="FACEUP-DRAW-RESOURCE-CARD",
                    instruction="draw a faceup unit",
                    allotted_seconds=allotted_seconds,
                    allotted_since_action_idx=allotted_since_action_idx,
                    faceup_draw=LegalActionFaceupDraw(
                        deck_idx=0,
                        card_name=card_name,
                    )
                )
            )

    for legal_action in get_legal_actions_for_paths(state_kernel, player_idx):
        legal_actions = legal_actions.append(legal_action)
    
    return legal_actions


@dispatch(State, bool)
def get_md(s, compact: bool=True):
    return get_md(s, get_default_toplay(s), compact)


@dispatch(State, int, bool)
def get_md(s: State, player_idx: int, compact: bool=True):
    player_state = PlayerState(
        game_config=getpublicgameconfig(s.game_config),
        public=getpublicstate(s),
        private=getprivatestate(s, player_idx)
    )
    return get_md(player_state, compact)


@dispatch(PlayerState, bool)
def get_md(player_state: PlayerState, compact: bool=True):
    player_idx = player_state.private.player.idx
    config = player_state.game_config
    public = player_state.public
    private = player_state.private
    player_name_list = [
        f"player-{p_idx}"
        for p_idx in range(config.num_players)
    ]
    inputs = {
        "num_players": config.num_players,
        "num_legal_actions": len(private.legal_actions),
        "game_name": "Melee",
        "inspiration_game_name": "Ticket to Ride",
        "player_idx": player_idx,
        "player_name_list": player_name_list,
        "game_config_json": json.dumps(config.to_llm_dict(), indent=(None if compact else 2), separators=(',', ':')),
        "public_game_state_json": json.dumps(public.to_llm_dict(), indent=(None if compact else 2), separators=(',', ':')),
        "private_game_state_json": json.dumps(private.to_llm_dict(), indent=(None if compact else 2), separators=(',', ':')),
    }
    # Read in "llm.md" as a string
    md_template = read_file_as_string("llm.md")
    codes = [x.code for x in private.legal_actions]
    return md_template.format(**inputs), codes


def read_file_as_string(file_path):
    # Get the directory where this fns.py file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the file
    absolute_path = os.path.join(current_dir, file_path)
    with open(absolute_path, 'r') as file:
        return file.read()