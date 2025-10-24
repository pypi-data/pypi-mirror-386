from __future__ import annotations

from collections.abc import Generator
from typing import Any

from ._service import get_service


class User:
    def __init__(self, data: dict[str, Any]):
        self.name: str = data["realname"]
        self.id: str = data["id"]
        self.gender: str = data["sex_dictText"]
        self.avatar: str | None = data["avatar"]
        self.grade: str = data["grade"]
        self.college: str | None = data["college"]
        self.classes: str = data["classes"]
        self.scientificValue: int = data["scientificqiValue"]
        self.birthday: str = data["birthday"]

    @property
    def phone(self) -> str | None:
        if not hasattr(self, "_phone"):
            url = "/sys/user/querySysUser"
            params = {"username": self.id}
            try:
                self._phone = get_service().get_result(url, params)["phone"]
            except RuntimeError as e:
                if e.args[0] == "验证失败":
                    self._phone = None
                else:
                    raise e
        return self._phone

    def __repr__(self):
        return f"<User {self.id} {self.name!r}>"

    @classmethod
    def find(
        cls, name_or_id: str, max: int = -1, size: int = 50
    ) -> Generator[User, None, None]:
        url = "sys/user/getPersonInChargeUser"
        params = {"realname": name_or_id}
        yield from map(User, get_service().page_search(url, params, max, size))

    @classmethod
    def get(cls, id: str | None = None):
        phone = None
        if not id:
            info: dict[str, str] = get_service().get_result("paramdesign/scMyInfo/info")
            id = info["username"]
            phone = info["phone"]
        stds = list(cls.find(id, 2, 2))
        if len(stds) != 1:
            raise RuntimeError("Failed to get the user")
        user = stds[0]
        if phone:
            user._phone = phone
        return user
