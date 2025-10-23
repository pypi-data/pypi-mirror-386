from fastapi import Depends, HTTPException, Request

import koco_product_sqlmodel.dbmodels.definition as sqlm
import koco_product_sqlmodel.mdb_connect.generic_object_connect as mdb_gen
import koco_product_sqlmodel.mdb_connect.mdb_connector as mdb_con
import koco_product_sqlmodel.fastapi.routes.generic_route as rgen
import koco_product_sqlmodel.fastapi.routes.security as rsec
from koco_product_sqlmodel.mdb_connect.import_excel import log_changes


class SpecTableRoute(rgen.ParentRoute):
    def __init__(
        self,
        sqlmodel_db: sqlm.SQLModel,
        sqlmodel_post: sqlm.SQLModel,
        sqlmodel_get: sqlm.SQLModel,
        tags: list[str],
    ):
        super().__init__(
            sqlmodel_db=sqlmodel_db,
            sqlmodel_post=sqlmodel_post,
            sqlmodel_get=sqlmodel_get,
            tags=tags,
        )

    async def post_object(
        self, object: sqlm.CSpecTablePost, request: Request
    ) -> sqlm.SQLModel:
        object.user_id = await rsec.get_user_id_from_request(request=request)
        new_obj = mdb_gen.post_object(db_obj=self.sqlmodel_db(**object.model_dump()))
        return await self.get_and_log_updated_model(
            request=request, updated_object=new_obj
        )

    async def patch_object(
        self, id: int, obj: sqlm.CSpecTablePost, request: Request
    ) -> sqlm.SQLModel:
        obj.user_id = await rsec.get_user_id_from_request(request=request)
        updated_object = mdb_gen.patch_object(
            id=id, db_obj=obj, db_obj_type=self.sqlmodel_db
        )
        if updated_object == None:
            raise HTTPException(status_code=404, detail="Object not found")
        return await self.get_and_log_updated_model(
            request=request, updated_object=updated_object
        )

    async def delete_object(
        self, id: int, delete_recursive: bool = True, request: Request = None
    ) -> dict[str, bool]:
        """
        Delete an spectable by cspectable.id.

        * Request parameter: *delete_recursive* = true

        If set to *true* all subitems contained in given spectable will be removed from database to avoid orphaned data
        """
        user_id = await rsec.get_user_id_from_request(request=request)
        mdb_con.delete_spectable_by_id(
            log_func=log_changes, spectable_id=id, delete_connected_items=delete_recursive, user_id=user_id
        )
        return {"ok": True}


route_spectable = SpecTableRoute(
    sqlmodel_db=sqlm.CSpecTable,
    sqlmodel_get=sqlm.CSpecTableGet,
    sqlmodel_post=sqlm.CSpecTablePost,
    tags=["Endpoints to SPECTABLE-data"],
)


class SpecTableItemRoute(SpecTableRoute):
    def __init__(
        self,
        sqlmodel_db: sqlm.SQLModel,
        sqlmodel_post: sqlm.SQLModel,
        sqlmodel_get: sqlm.SQLModel,
        tags: list[str],
    ):
        super().__init__(
            sqlmodel_db=sqlmodel_db,
            sqlmodel_post=sqlmodel_post,
            sqlmodel_get=sqlmodel_get,
            tags=tags,
        )
        self.router.add_api_route(
            path="/batch/",
            endpoint=self.post_objects_batch,
            methods=["POST"],
            dependencies=[Depends(rsec.has_post_rights)],
            response_model=list[self.sqlmodel_get],
        )
        self.router.add_api_route(
            path="/batch/",
            endpoint=self.patch_objects_batch,
            methods=["PATCH"],
            dependencies=[Depends(rsec.has_post_rights)],
            response_model=list[self.sqlmodel_get],
        )
        self.router.add_api_route(
            path="/batch/",
            endpoint=self.delete_objects_batch,
            methods=["DELETE"],
            dependencies=[Depends(rsec.has_post_rights)],
        )
        self.router.routes = sorted(
            self.router.routes,
            key=lambda route: "{" in getattr(route, "path", ""),
        )

    def get_objects(self, spec_table_id: int) -> list[sqlm.SQLModel]:
        """
        GET list of spectable items from DB.
        Parameter:
        * *spectable_id* - id of parent object
        * *parent* - parent object type
        """
        objects = mdb_gen.get_objects_from_spec_table(
            db_obj_type=self.sqlmodel_db, spec_table_id=spec_table_id
        )
        objects_get: list[type[sqlm.SQLModel]] = []
        for object in objects:
            objects_get.append(self.sqlmodel_get(**object.model_dump()))
        return objects_get

    async def post_object(
        self, object: sqlm.CSpecTableItemPost, request: Request
    ) -> sqlm.SQLModel:
        object.user_id = await rsec.get_user_id_from_request(request=request)
        new_obj = mdb_gen.post_object(db_obj=self.sqlmodel_db(**object.model_dump()))
        return await self.get_and_log_updated_model(
            request=request, updated_object=new_obj
        )

    async def patch_object(
        self, id: int, obj: sqlm.CSpecTableItemPost, request: Request
    ) -> sqlm.SQLModel:
        obj.user_id = await rsec.get_user_id_from_request(request=request)
        updated_object = mdb_gen.patch_object(
            id=id, db_obj=obj, db_obj_type=self.sqlmodel_db
        )
        if updated_object == None:
            raise HTTPException(status_code=404, detail="Object not found")
        return await self.get_and_log_updated_model(
            request=request, updated_object=updated_object
        )

    async def post_objects_batch(
        self, objects: list[sqlm.CSpecTableItemPost], request: Request
    ) -> list[sqlm.SQLModel]:
        if not objects:
            return []
        user_id = await rsec.get_user_id_from_request(request=request)
        db_objects = []
        for object in objects:
            object.user_id = user_id
            db_objects.append(self.sqlmodel_db(**object.model_dump()))
        created_objects = mdb_gen.post_objects(db_objs=db_objects)
        results: list[sqlm.SQLModel] = []
        for created_object in created_objects:
            results.append(
                await self.get_and_log_updated_model(
                    request=request, updated_object=created_object
                )
            )
        return results

    async def patch_objects_batch(
        self, objects: list[sqlm.CSpecTableItemPatch], request: Request
    ) -> list[sqlm.SQLModel]:
        if not objects:
            return []
        user_id = await rsec.get_user_id_from_request(request=request)
        updates: list[tuple[int, dict[str, object]]] = []
        for object in objects:
            update_payload = object.model_dump(exclude_unset=True)
            object_id = update_payload.pop("id", None)
            if object_id == None:
                raise HTTPException(status_code=422, detail="Missing id in payload")
            update_payload["user_id"] = user_id
            updates.append((object_id, update_payload))
        updated_objects, missing_ids = mdb_gen.patch_objects(
            db_obj_type=self.sqlmodel_db, updates=updates
        )
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"SpecTableItems not found for ids: {sorted(missing_ids)}",
            )
        results: list[sqlm.SQLModel] = []
        for updated_object in updated_objects:
            results.append(
                await self.get_and_log_updated_model(
                    request=request, updated_object=updated_object
                )
            )
        return results

    async def delete_objects_batch(
        self, payload: sqlm.CSpecTableItemBatchDelete, request: Request
    ) -> dict[str, bool]:
        user_id = await rsec.get_user_id_from_request(request=request)
        missing_ids = mdb_con.delete_spectableitems_by_id(
            log_func=log_changes,
            spectableitem_ids=payload.ids,
            user_id=user_id,
        )
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"SpecTableItems not found for ids: {sorted(missing_ids)}",
            )
        return {"ok": True}

    async def delete_object(
        self, id: int, request: Request = None
    ) -> dict[str, bool]:
        """
        Delete an spectable-item by cspectableitem.id.
        """
        user_id = await rsec.get_user_id_from_request(request=request)
        mdb_con.delete_spectableitem_by_id(
            log_func=log_changes, spectableitem_id=id, user_id=user_id
        )
        return {"ok": True}



route_spectableitem = SpecTableItemRoute(
    sqlmodel_db=sqlm.CSpecTableItem,
    sqlmodel_get=sqlm.CSpecTableItemGet,
    sqlmodel_post=sqlm.CSpecTableItemPost,
    tags=["Endpoints to SPECTABLEITEM-data"],
)


def main():
    pass


if __name__ == "__main__":
    main()
