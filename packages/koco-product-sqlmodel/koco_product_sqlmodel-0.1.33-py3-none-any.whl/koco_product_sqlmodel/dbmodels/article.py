from datetime import datetime
from sqlalchemy import Column
from typing import Optional
from sqlalchemy.types import TIMESTAMP

from sqlmodel import Field, SQLModel, text
from sqlmodel.main import Relationship

import koco_product_sqlmodel.dbmodels.models_enums as m_enum


class CArticlePost(SQLModel):
    article: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=4096)
    short_description: str | None = Field(default=None, max_length=1024)
    family_id: int | None = Field(default=None, foreign_key="cfamily.id")
    status: int = Field(
        default=m_enum.StatusEnum.in_work.value
    )  # general status of the data set 1: "in work", 2: "ready for review". 3: "released"
    order_priority: int = Field(default=100)  # order priority for the article, used for sorting in the frontend
    user_id: int = Field(default=1, foreign_key="cuser.id")


class CArticleGet(CArticlePost):
    id: int | None = None
    upddate: datetime | None = None
    insdate: datetime | None = None


class CArticle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    article: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=4096)
    short_description: str | None = Field(default=None, max_length=1024)
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
    family_id: int | None = Field(default=None, foreign_key="cfamily.id")
    status: int = Field(
        default=m_enum.StatusEnum.in_work.value
    )  # general status of the data set 1: "in work", 2: "ready for review". 3: "released"
    user_id: int = Field(default=1, foreign_key="cuser.id")
    order_priority: int = Field(default=100)  # order priority for the article, used for sorting in the frontend
    family: Optional["CFamily"] = Relationship(back_populates="articles")


def main():
    pass


if __name__ == "__main__":
    main()
