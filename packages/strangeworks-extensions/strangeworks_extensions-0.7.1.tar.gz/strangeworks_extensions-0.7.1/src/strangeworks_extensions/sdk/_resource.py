"""resources.py."""

from typing import List, Optional

from strangeworks_core.errors.error import StrangeworksError
from strangeworks_core.platform.gql import Operation
from strangeworks_core.types.resource import Resource

from strangeworks_extensions.sdk._gql import SDKAPI

_get_op = Operation(
    query="""
query sdk_get_resources($product_slugs: [String!], $first: Int, $after: ID) {
  workspace {
    resources(
      productSlugs: $product_slugs
      pagination: {after: $after, first: $first}
    ) {
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        cursor
        node {
          slug
          product {
            slug
          }
          configurations {
            key
            type
            valueJson
          }
          status
        }
      }
    }
  }
}
    """
)


def get(
    client: SDKAPI,
    resource_slug: Optional[str] = None,
    product_slug: str | None = None,
    batch_size: int = 50,
) -> List[Resource]:
    """Retrieve a list of available resources.

    Parameters
    ----------
    client: StrangeworksGQLClient
        client to access the sdk api on the platform.
    resource_slug: Optional[str]
        If supplied, only the resource whose slug matches will be returned. Defaults to
        None.
    batch_size: int
        Number of jobs to retrieve with each request. Defaults to 50.

    Return
    ------
    Optional[List[Resource]]
        List of resources or None if workspace has no resources configured.
    """
    hasNextPage: bool = True
    cursor: str | None = None
    resources: list[Resource] = []

    while hasNextPage:
        workspace = client.execute(
            op=_get_op,
            product_slugs=[product_slug],
            first=batch_size,
            after=cursor,
        ).get("workspace")

        if not workspace:
            raise StrangeworksError(
                message="unable to retrieve jobs information (no workspace returned)"
            )

        page_info = workspace.get("resources").get("pageInfo")
        cursor = page_info.get("endCursor")
        hasNextPage = page_info.get("hasNextPage")

        resource_obj = workspace.get("resources", [])
        if resource_obj:
            edges = resource_obj.get("edges", [])
            for x in edges:
                node = x.get("node")
                if node:
                    res = Resource(**node)
                    resources.append(res)

                    if resource_slug and res.slug == resource_slug:
                        # we are looking for a specific resource(s)
                        # found resource. append to list and return
                        resources.append(res)
                        hasNextPage = False
                        break

        if resource_slug and resources:
            resources = [res for res in resources if res.slug == resource_slug]

        page_info = workspace.get("resources").get("pageInfo")
        cursor = page_info.get("endCursor")
        hasNextPage = page_info.get("hasNextPage")

    return resources
