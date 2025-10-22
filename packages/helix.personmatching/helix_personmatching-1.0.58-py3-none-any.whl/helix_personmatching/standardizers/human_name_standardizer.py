from typing import Optional, List, cast

from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.fhirtypes import String, HumanNameType
from nominally import parse_name

from helix_personmatching.fhir_manager.parse_name_result import ParseNameResult
from helix_personmatching.standardizers.human_name_standardizer_result import (
    HumanNameStandardizerResult,
)
from helix_personmatching.utils.list_utils import get_first_element_or_null


class HumanNameStandardizer:
    @staticmethod
    def standardize(
        *,
        names: list[HumanName] | None,
        capitalize: bool = False,
        verbose: bool = False,
    ) -> list[HumanNameStandardizerResult] | None:
        """
        Standardize a list of human names

        :param names: List of HumanName objects to standardize
        :param capitalize: Whether to capitalize the names
        :param verbose: Whether to print verbose output
        :return: List of HumanNameStandardizerResult objects
        """
        if not names:
            return None

        assert isinstance(names, list)

        return [
            n
            for n in [
                HumanNameStandardizer.standardize_single(
                    name=name, verbose=verbose, capitalize=capitalize
                )
                for name in names
            ]
            if n is not None
        ]

    @staticmethod
    def standardize_single(
        *, name: HumanName | None, capitalize: bool = False, verbose: bool = False
    ) -> HumanNameStandardizerResult | None:
        """
        Standardize a single human name

        :param name: HumanName object to standardize
        :param capitalize: Whether to capitalize the names
        :param verbose: Whether to print verbose output
        :return: HumanNameStandardizerResult object
        """
        if not name:
            return None

        assert isinstance(name, HumanName)

        first_name: Optional[str] = (
            str(name.given[0]) if name and name.given and len(name.given) > 0 else None
        )
        family_name: Optional[str] = str(name.family) if name and name.family else None
        middle_name: Optional[str] = (
            str(name.given[1]) if name and name.given and len(name.given) > 1 else None
        )
        # convert FHIR String list to plain list[str]
        suffix: List[str] | None = (
            [str(s) for s in name.suffix] if name.suffix else None
        )
        prefix: List[str] | None = (
            [str(p) for p in name.prefix] if name.prefix else None
        )

        # try to parse names using nominally since the names can be stored in wrong fields
        parsed_name: Optional[ParseNameResult] = HumanNameStandardizer.safe_name_parse(
            name=name,
            verbose=verbose,
        )
        if parsed_name is not None:
            if parsed_name.first:
                first_name = (
                    parsed_name.first.title() if capitalize else parsed_name.first
                )
            if parsed_name.middle:
                middle_name = (
                    parsed_name.middle.title() if capitalize else parsed_name.middle
                )
            if parsed_name.last:
                family_name = (
                    parsed_name.last.title() if capitalize else parsed_name.last
                )

            if parsed_name.title:
                parsed_name.title = (
                    parsed_name.title.title() if capitalize else parsed_name.title
                )

            if parsed_name.suffix:
                if isinstance(parsed_name.suffix, str):
                    parsed_suffix = [s for s in parsed_name.suffix.split(" ")]
                elif isinstance(parsed_name.suffix, list):
                    parsed_suffix = [str(s) for s in parsed_name.suffix]
                else:
                    parsed_suffix = []
                suffix = parsed_suffix

            if parsed_name.prefix and parsed_name.title:
                if isinstance(parsed_name.prefix, str):
                    parsed_prefix = [s for s in parsed_name.prefix.split(" ")]
                elif isinstance(parsed_name.prefix, list):
                    parsed_prefix = [str(s) for s in parsed_name.prefix]
                else:
                    parsed_prefix = []
                prefix = parsed_prefix + [str(parsed_name.title)]
            elif parsed_name.title:
                prefix = [str(parsed_name.title)]

        name_parts: List[str] = []
        if prefix:
            name_parts.extend([str(p) for p in prefix])
        if first_name:
            name_parts.append(first_name)
        if middle_name:
            name_parts.append(middle_name)
        if family_name:
            name_parts.append(family_name)
        if suffix:
            name_parts.extend([str(s) for s in suffix])
        name_text = " ".join(name_parts) if name_parts and len(name_parts) > 0 else None

        standardized_name: HumanName = name.copy()
        if first_name:
            standardized_name.given = cast(
                List[String | None], [cast(String, first_name)]
            )
        if middle_name:
            # ensure the given is initialized as expected list type
            if not standardized_name.given:
                standardized_name.given = cast(List[String | None], [])
            assert standardized_name.given is not None
            standardized_name.given.append(cast(String, middle_name))
        if family_name:
            standardized_name.family = cast(String, family_name)
        if name_text:
            standardized_name.text = cast(String, name_text)
        if suffix:
            standardized_name.suffix = cast(List[String | None], suffix)
        if prefix:
            standardized_name.prefix = cast(List[String | None], prefix)

        nick_name = parsed_name.nickname if parsed_name else None
        if nick_name and capitalize:
            nick_name = nick_name.title()

        middle_initial = (
            middle_name[0] if middle_name and len(middle_name) > 0 else None
        )

        return HumanNameStandardizerResult(
            name=cast(HumanNameType, standardized_name),
            middle_initial=middle_initial,
            nick_name=nick_name,
        )

    @staticmethod
    def safe_name_parse(
        *,
        name: Optional[HumanName],
        verbose: bool = False,
    ) -> Optional[ParseNameResult]:
        # noinspection PyUnresolvedReferences
        if name is None:
            return None

        assert isinstance(name, HumanName)

        if verbose:
            print("FhirToAttributeDict:safe_name_parse()...")

        combined_name = ""
        try:
            # if both family and given are populated then ignore text
            if name.given is not None and len(name.given) > 0 and name.family:
                combined_name += " ".join([str(g) for g in name.given])
                combined_name += f" {name.family}"
            elif name.text is not None:
                combined_name = name.text

            if not combined_name:
                return None
            result = parse_name(combined_name)
            return ParseNameResult(
                first=result.get("first"),
                middle=result.get("middle"),
                last=result.get("last"),
                title=result.get("title"),
                suffix=result.get("suffix"),
                prefix=result.get("prefix"),
                nickname=result.get("nickname"),
            )
        except Exception as e:
            if verbose:
                print(f"Exception (returning None): Parsing Name: {combined_name}: {e}")

            return None

    @staticmethod
    def get_primary_human_name(
        *, name: Optional[List[HumanNameType]]
    ) -> Optional[HumanName]:
        """
        Get the primary human name from a list of human names

        :param name: List of HumanName objects
        :return: HumanName object
        """
        if name is None:
            return None

        # The order of preference is:
        # https://hl7.org/FHIR/valueset-name-use.html
        # 1. usual
        # 2. official
        # 3. maiden
        # 4. others
        usual_name: Optional[HumanName] = get_first_element_or_null(
            [name1 for name1 in name if name1.use == "usual"]
        )
        if usual_name:
            return usual_name

        official_name: Optional[HumanName] = get_first_element_or_null(
            [name1 for name1 in name if name1.use == "official"]
        )
        if official_name:
            return official_name

        maiden_name: Optional[HumanName] = get_first_element_or_null(
            [name1 for name1 in name if name1.use == "maiden"]
        )
        if maiden_name:
            return maiden_name

        return cast(Optional[HumanName], get_first_element_or_null(name))

    @staticmethod
    def standardize_text(
        *,
        name: Optional[str],
        capitalize: bool = False,
    ) -> HumanNameStandardizerResult | None:
        """
        Standardize a full name and return the result object

        :param name: Full name to standardize
        :param capitalize: Whether to capitalize the names
        :return: HumanNameStandardizerResult object
        """
        if not name:
            return HumanNameStandardizerResult(
                name=None, middle_initial=None, nick_name=None
            )

        assert isinstance(name, str)

        result = HumanNameStandardizer.standardize_single(
            name=HumanName.validate({"text": name}),
            capitalize=capitalize,
        )

        return result

    @staticmethod
    def standardize_text_simple(
        *,
        name: Optional[str],
        capitalize: bool = False,
    ) -> Optional[str]:
        """
        Standardize a full name and return the text

        :param name: Full name
        :param capitalize: Whether to capitalize the names
        """
        if not name:
            return None

        assert isinstance(name, str)

        result = HumanNameStandardizer.standardize_text(
            name=name, capitalize=capitalize
        )

        return result.name.text if result and result.name else None
