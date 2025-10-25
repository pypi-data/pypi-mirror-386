from datetime import datetime
from typing import Optional
from sqlalchemy import Column
from sqlalchemy.types import TIMESTAMP

from sqlmodel import Field, SQLModel, text


class CCategoryTreePost(SQLModel):
    category: str|None = Field(default=None, max_length=128)
    export_target: str|None = Field(default=None, max_length=16)
    description: str|None = Field(default=None, max_length=4096)
    parent_id: int|None = Field(default=None)
    pos: int|None = Field(default=1)
    user_id: int = Field(default=1, foreign_key="cuser.id")


class CCategoryTreeGet(CCategoryTreePost):
    id: Optional[int] = Field(default=None, primary_key=True)
    upddate: datetime = Field(
        sa_column=Column(
            TIMESTAMP,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        )
    )
    insdate: datetime = Field(
        sa_column=Column(
            TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
        )
    )

class CCategoryTree(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str|None = Field(default=None, max_length=128)
    export_target: str|None = Field(default=None, max_length=16)
    description: str|None = Field(default=None, max_length=4096)
    parent_id: int|None = Field(default=None)
    pos: int|None = Field(default=1)
    user_id: int = Field(default=1, foreign_key="cuser.id")
    upddate: datetime = Field(
        sa_column=Column(
            TIMESTAMP,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        )
    )
    insdate: datetime = Field(
        sa_column=Column(
            TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
        )
    )


class CCategoryMapperPost(SQLModel):
    category_id: Optional[int] = Field(default=None, foreign_key="ccategorytree.id")
    family_id: Optional[int] = Field(default=None, foreign_key="cfamily.id")
    user_id: int = Field(default=1, foreign_key="cuser.id")

class CCategoryMapperGet(CCategoryMapperPost):
    id: Optional[int] = Field(default=None, primary_key=True)
    upddate: datetime = Field(
        sa_column=Column(
            TIMESTAMP,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        )
    )
    insdate: datetime = Field(
        sa_column=Column(
            TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
        )
    )


class CCategoryMapper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: Optional[int] = Field(default=None, foreign_key="ccategorytree.id")
    family_id: Optional[int] = Field(default=None, foreign_key="cfamily.id")
    user_id: int = Field(default=1, foreign_key="cuser.id")
    upddate: datetime = Field(
        sa_column=Column(
            TIMESTAMP,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        )
    )
    insdate: datetime = Field(
        sa_column=Column(
            TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
        )
    )


def main():
    pass


if __name__ == "__main__":
    main()
