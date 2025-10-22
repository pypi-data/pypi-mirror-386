from importlib.resources import files

from typing import Set, Dict, List

from nicknames import NickNamer, NameTriplet


class NickNameLoader:
    @staticmethod
    def load_nick_names() -> Dict[str, Set[str]]:
        # Open the file using the new files() API
        with files(__package__).joinpath("nick_name_overrides.csv").open() as f:
            contents: str = f.read()
            lines: List[str] = contents.splitlines()
            name_triplets: List[NameTriplet] = []
            for line in lines:
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                name_triplets.append(
                    NameTriplet(
                        name1=parts[0].strip(),
                        relationship="has_nickname",
                        name2=parts[1].strip(),
                    )
                )

            nick_namer_from_triplets = NickNamer.from_triplets(name_triplets)
            nickname_overrides: Dict[str, Set[str]] = (
                nick_namer_from_triplets.nickname_lookup
            )
            nickname_lookup: Dict[str, Set[str]] = NickNamer.default_lookup()
            # now add the overrides
            for key, value in nickname_overrides.items():
                if key in nickname_lookup:
                    nickname_lookup[key] = nickname_lookup[key] | value
                else:
                    nickname_lookup[key] = value
            return nickname_lookup
