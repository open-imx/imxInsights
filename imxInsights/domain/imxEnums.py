from enum import Enum


class Imx12ProjectDisciplineEnum(Enum):
    UNKNOWN = "Unknown"
    STANDARD_VERIFICATION_SURVEY = "StandardVerificationSurvey"
    NON_STANDARD_VERIFICATION_SURVEY = "NonStandardVerificationSurvey"
    AREA_UPDATE = "AreaUpdate"
    LOGISTICS_AREAS = "LogisticsAreas"
    TRAIN_MOVEMENT_AND_ROUTE_DESIGN = "TrainMovementAndRouteDesign"
    SIGNALING_DESIGN = "SignalingDesign"

    @classmethod
    def from_string(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")  # noqa: TRY003


class Imx12DataExchangePhaseEnum(Enum):
    UNKNOWN = "Unknown"
    FUNCTIONAL_DESIGN = "FunctionalDesign"
    CONCEPT_OF_PRELIMINARY_DESIGN = "ConceptOfPreliminaryDesign"
    PRELIMINARY_DESIGN = "PreliminaryDesign"
    FINAL_DESIGN = "FinalDesign"
    VERIFICATION = "Verification"

    @classmethod
    def from_string(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")  # noqa: TRY003
