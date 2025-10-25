from typing import Any, Sequence, Tuple

import sqlmodel as sqlm
import koco_product_sqlmodel.mdb_connect.mdb_connector as mdb_con


def get_family_related_objects(
    db_obj_type: sqlm.SQLModel, family_id: int | None
) -> list[sqlm.SQLModel]:
    if family_id == None:
        statement = sqlm.select(db_obj_type)
    else:
        statement = sqlm.select(db_obj_type).where(db_obj_type.family_id == family_id)
    with sqlm.Session(mdb_con.mdb_engine) as session:
        return session.exec(statement=statement).all()


def get_objects_from_parent(
    db_obj_type: sqlm.SQLModel, parent_id: int | None, parent: str | None
) -> list[sqlm.SQLModel]:
    if parent_id == None and parent == None:
        statement = sqlm.select(db_obj_type)
    elif parent_id != None and parent == None:
        statement = sqlm.select(db_obj_type).where(db_obj_type.parent_id == parent_id)
    elif parent_id == None and parent != None:
        statement = sqlm.select(db_obj_type).where(db_obj_type.parent == parent)
    else:
        statement = (
            sqlm.select(db_obj_type)
            .where(db_obj_type.parent_id == parent_id)
            .where(db_obj_type.parent == parent)
        )
    with sqlm.Session(mdb_con.mdb_engine) as session:
        return session.exec(statement=statement).all()


def get_objects_from_spec_table(
    db_obj_type: sqlm.SQLModel, spec_table_id: int | None
) -> list[sqlm.SQLModel]:
    if spec_table_id == None:
        return
    else:
        statement = sqlm.select(db_obj_type).where(
            db_obj_type.spec_table_id == spec_table_id
        )
    with sqlm.Session(mdb_con.mdb_engine) as session:
        return session.exec(statement=statement).all()


def get_object(db_obj_type: sqlm.SQLModel, id: int | None) -> sqlm.SQLModel:
    if id == None:
        return
    statement = sqlm.select(db_obj_type).where(db_obj_type.id == id)
    with sqlm.Session(mdb_con.mdb_engine) as session:
        return session.exec(statement=statement).one_or_none()


def post_object(db_obj: sqlm.SQLModel):
    with sqlm.Session(mdb_con.mdb_engine) as session:
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
    return db_obj


def post_objects(db_objs: Sequence[sqlm.SQLModel]) -> list[sqlm.SQLModel]:
    if not db_objs:
        return []
    with sqlm.Session(mdb_con.mdb_engine) as session:
        for db_obj in db_objs:
            session.add(db_obj)
        session.commit()
        for db_obj in db_objs:
            session.refresh(db_obj)
    return list(db_objs)


def patch_object(id: int, db_obj: sqlm.SQLModel, db_obj_type: sqlm.SQLModel):
    statement = sqlm.select(db_obj_type).where(db_obj_type.id == id)
    with sqlm.Session(mdb_con.mdb_engine) as session:
        res = session.exec(statement=statement).one_or_none()
        if res == None:
            return
        res.sqlmodel_update(db_obj.model_dump(exclude_unset=True))
        session.add(res)
        session.commit()
        session.refresh(res)
    return res


def patch_objects(
    db_obj_type: sqlm.SQLModel,
    updates: Sequence[Tuple[int, dict[str, Any]]],
) -> tuple[list[sqlm.SQLModel], set[int]]:
    if not updates:
        return [], set()
    ids = [obj_id for obj_id, _ in updates]
    with sqlm.Session(mdb_con.mdb_engine) as session:
        statement = sqlm.select(db_obj_type).where(db_obj_type.id.in_(ids))
        res = session.exec(statement=statement).all()
        res_map = {obj.id: obj for obj in res}
        missing_ids = set(ids).difference(res_map.keys())
        if missing_ids:
            return [], missing_ids
        for obj_id, payload in updates:
            db_obj = res_map[obj_id]
            if payload:
                db_obj.sqlmodel_update(payload)
            session.add(db_obj)
        session.commit()
        for db_obj in res_map.values():
            session.refresh(db_obj)
    ordered_results = [res_map[obj_id] for obj_id in ids]
    return ordered_results, set()


def delete_object(db_obj_type: sqlm.SQLModel, id: int) -> int | None:
    statement = sqlm.select(db_obj_type).where(db_obj_type.id == id)
    with sqlm.Session(mdb_con.mdb_engine) as session:
        res = session.exec(statement=statement).one_or_none()
        if res == None:
            return
        session.delete(res)
        session.commit()
        return 1


def main():
    pass


if __name__ == "__main__":
    main()
