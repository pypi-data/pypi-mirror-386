from __future__ import annotations

import re


class PWDatabase:
    def __init__(self, db: str | dict[str, str], match: str | None = None) -> None:
        if isinstance(db, str):
            self.db = {}
            self.default: str | None = db

        else:
            self.db = db
            self.default = None
            self.init()

        self.match = re.compile(match) if match else None

    def init(self) -> None:
        for email, pwd in self.db.items():
            if email == "*":
                self.default = pwd
                del self.db["*"]
                return

    def password(self, email: str) -> str | None:
        if self.match is not None and not self.match.match(email):
            return None
        return self.db.get(email, self.default)

    def isvalid(self, email: str) -> bool:
        if "@" not in email:
            return False
        if self.match is not None and not self.match.match(email):
            return False
        if email in self.db:
            return True
        if self.default is not None:
            return True
        return False

    @property
    def need_email(self):
        return len(self.db) > 0
