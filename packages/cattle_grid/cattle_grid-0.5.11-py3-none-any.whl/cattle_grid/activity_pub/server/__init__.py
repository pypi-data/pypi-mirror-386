"""This package contains the overall router for all connection
needs to the Fediverse. This means the .well-known endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Header

from typing import Annotated

from bovine.utils import webfinger_response
from bovine.types.jrd import JrdData, JrdLink
from bovine.types.nodeinfo import NodeInfo, Software
from sqlalchemy import select

from cattle_grid.dependencies.fastapi import SqlSession
from cattle_grid.database.activity_pub_actor import PublicIdentifier
from cattle_grid.version import __version__
from cattle_grid.tools.fastapi import JrdResponse

from .router import ap_router
from .router_inbox import ap_router_inbox
from .router_object import ap_router_object


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ap")
router.include_router(ap_router)
router.include_router(ap_router_inbox)
router.include_router(ap_router_object)


@router.get("/", include_in_schema=False)
async def main() -> str:
    return "cattle_grid ap endpoint"


@router.get("/.well-known/webfinger", response_class=JrdResponse, tags=["fediverse"])
async def webfinger_responder(resource: str, session: SqlSession) -> JrdData:
    """Handles requests to .well-known/webfinger. Results are determined
    by the identifier property of [PublicIdentifier][cattle_grid.database.activity_pub_actor.PublicIdentifier] matching the resource
    parameter.

    See [RFC 7033 WebFinger](https://www.rfc-editor.org/rfc/rfc7033).
    """

    logger.info("looking up web finger for resource '%s'", resource)

    pi = await session.scalar(
        select(PublicIdentifier).where(PublicIdentifier.identifier == resource)
    )

    if not pi:
        raise HTTPException(status_code=404, detail="Item not found")

    return webfinger_response(pi.identifier, pi.actor.actor_id)


@router.get(
    "/.well-known/nodeinfo",
    response_model_exclude_none=True,
    response_class=JrdResponse,
    tags=["fediverse"],
)
async def nodeinfo_responder(x_ap_location: Annotated[str, Header()]) -> JrdData:
    return JrdData(
        links=[
            JrdLink(
                type="http://nodeinfo.diaspora.software/ns/schema/2.0",
                href=x_ap_location + "_2.0",
            )  # type: ignore
        ]
    )  # type: ignore


@router.get("/.well-known/nodeinfo_2.0", response_class=JrdResponse, tags=["fediverse"])
async def nodeinfo_data_responder() -> NodeInfo:
    """Returns the information according to the nodeinfo spec"""
    return NodeInfo(software=Software(name="cattle-grid", version=__version__))  # type: ignore
