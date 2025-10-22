from enum import Enum, auto

from _qwak_proto.qwak.feature_store.features.execution_pb2 import (
    LARGE as ProtoLARGE,
    MEDIUM as ProtoMEDIUM,
    NANO as ProtoNANO,
    SMALL as ProtoSMALL,
    XLARGE as ProtoXLARGE,
    XXLARGE as ProtoXXLARGE,
    XXXLARGE as ProtoXXXLARGE,
    ClusterTemplate as ProtoClusterTemplate,
)


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class ClusterTemplate(AutoName):
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    XLARGE = auto()
    XXLARGE = auto()
    XXXLARGE = auto()
    NANO = auto()

    _cluster_template_to_proto = {
        SMALL: ProtoSMALL,
        MEDIUM: ProtoMEDIUM,
        LARGE: ProtoLARGE,
        XLARGE: ProtoXLARGE,
        XXLARGE: ProtoXXLARGE,
        XXXLARGE: ProtoXXXLARGE,
        NANO: ProtoNANO,
    }

    _proto_to_cluster_template = {v: k for k, v in _cluster_template_to_proto.items()}

    @classmethod
    def from_proto(cls, proto: ProtoClusterTemplate):
        return cls(
            ClusterTemplate._proto_to_cluster_template.value[proto.cluster_template]
        )

    @classmethod
    def from_cluster_template_number(cls, cluster_template_number: int):
        return cls(
            ClusterTemplate._proto_to_cluster_template.value[cluster_template_number]
        )

    @staticmethod
    def to_proto(template):
        if not template:
            return None

        _cluster_template_to_proto = {
            ClusterTemplate.SMALL: ProtoSMALL,
            ClusterTemplate.MEDIUM: ProtoMEDIUM,
            ClusterTemplate.LARGE: ProtoLARGE,
            ClusterTemplate.XLARGE: ProtoXLARGE,
            ClusterTemplate.XXLARGE: ProtoXXLARGE,
            ClusterTemplate.XXXLARGE: ProtoXXXLARGE,
            ClusterTemplate.NANO: ProtoNANO,
        }
        return _cluster_template_to_proto[template]
