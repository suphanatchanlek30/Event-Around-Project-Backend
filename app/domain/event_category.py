class EventCategory:
    def __init__(self, category_id: int, name: str, description: str | None = None, is_active: bool = True):
        self._category_id = category_id
        self._name = ""
        self.set_name(name)
        self._description = description
        self._is_active = is_active

    def get_category_id(self) -> int:
        return self._category_id

    def get_name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("CATEGORY_NAME_REQUIRED")
        self._name = normalized_name

    def get_description(self) -> str | None:
        return self._description

    def set_description(self, description: str | None) -> None:
        self._description = description

    def get_is_active(self) -> bool:
        return self._is_active

    def deactivate(self) -> None:
        self._is_active = False
