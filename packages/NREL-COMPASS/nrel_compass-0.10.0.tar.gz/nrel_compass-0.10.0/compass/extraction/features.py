"""Ordinance mutually-exclusive features class"""

from compass.exceptions import COMPASSValueError


class SetbackFeatures:
    """Utility class to get mutually-exclusive feature descriptions"""

    DEFAULT_FEATURE_DESCRIPTIONS = {
        "structures": [
            "occupied dwellings",
            "buildings",
            "structures",
            "residences",
        ],
        "property line": [
            "property lines",
            "lot lines",
            "facility perimeters",
            "parcels",
            "subdivisions",
        ],
        "roads": ["roads"],  # , "rights-of-way"],
        "railroads": ["railroads"],
        "transmission": [
            "overhead electrical transmission lines",
            "overhead utility lines",
            "utility easements",
            "utility lines",
            "power lines",
            "electrical lines",
            "transmission lines",
        ],
        "water": ["lakes", "reservoirs", "streams", "rivers", "wetlands"],
    }
    """Aliases for mutually-exclusive setback features"""
    FEATURES_AS_IGNORE = {
        "structures": "structures",
        "property line": "property lines",
        "roads": "roads",
        "railroads": "railroads",
        "transmission": "transmission lines",
        "water": "wetlands",
    }
    """Features as they should appear in ignore phrases"""
    FEATURE_CLARIFICATIONS = {
        "structures": "",
        "property line": (
            "Dwelling units, structures, occupied buildings, residences, and "
            "other buildings **are not equivalent** to property lines or "
            "parcel boundaries unless the text **explicitly** makes that "
            "connection. "
        ),
        "roads": "Roads may also be labeled as rights-of-way. ",
        "railroads": "",
        "transmission": "",
        "water": "",
    }
    """Clarifications to add to feature prompts"""

    def __init__(self):
        self._validate_descriptions()

    def __iter__(self):
        for feature_id in self.DEFAULT_FEATURE_DESCRIPTIONS:
            feature, ignore = self._keep_and_ignore(feature_id)
            clarification = self.FEATURE_CLARIFICATIONS.get(feature_id, "")
            yield {
                "feature_id": feature_id,
                "feature": feature,
                "ignore_features": ignore,
                "feature_clarifications": clarification,
            }

    def _validate_descriptions(self):
        """Ensure all features have at least one description"""
        features_missing_descriptors = set()
        for feature, descriptions in self.DEFAULT_FEATURE_DESCRIPTIONS.items():
            if len(descriptions) < 1:
                features_missing_descriptors.add(feature)

        if any(features_missing_descriptors):
            msg = (
                f"The following features are missing descriptors: "
                f"{features_missing_descriptors}"
            )
            raise COMPASSValueError(msg)

    def _keep_and_ignore(self, feature_id):
        """Get the keep and ignore phrases for a feature"""
        keep_keywords = self.DEFAULT_FEATURE_DESCRIPTIONS[feature_id]
        ignore = [
            keyword
            for feat_id, keyword in self.FEATURES_AS_IGNORE.items()
            if feat_id != feature_id
        ]

        keep_phrase = _join_keywords(keep_keywords, final_sep=", and/or ")
        ignore_phrase = _join_keywords(ignore, final_sep=", and ")

        return keep_phrase, ignore_phrase


def _join_keywords(keywords, final_sep):
    """Join a list of keywords/descriptions"""
    if len(keywords) < 1:
        return ""

    if len(keywords) == 1:
        return keywords[0]

    comma_separated = ", ".join(keywords[:-1])
    return final_sep.join([comma_separated, keywords[-1]])
