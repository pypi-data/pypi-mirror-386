"""
reader.py

CENtreeReaderClient provides read-only access to ontologies in a CENtree server.
Supports entity lookups, label-based queries, tree navigation, and metadata inspection.
"""

import logging
from logging import NullHandler
from .base import CENtreeClient
from typing import Optional, Union

# ── Logging config ──────────────────────────────────────────
logger = logging.getLogger("scibite_toolkit.centree_clients.reader")
logger.addHandler(NullHandler())
# ────────────────────────────────────────────────────────────


class CENtreeReaderClient(CENtreeClient):
    """
    A client class for read-only operations on CENtree ontologies.
    Provides methods to query ontology metadata, entities, and perform lookups.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify: Union[bool, str] = True,
        **kwargs,
    ):
        super().__init__(base_url=base_url, bearer_token=bearer_token, verify=verify, **kwargs)
        logger.debug("Initialized CENtreeReaderClient base_url=%s", self.base_url)

    def get_classes_by_exact_label(self, ontology_id: str, label: str) -> list[dict]:
        """
        Retrieve ontology classes with an exact label match.

        Parameters
        ----------
        ontology_id : str
            Ontology ID to search within (e.g., "efo").
        label : str
            The exact label to match.

        Returns
        -------
        list[dict]
            List of matching entities (often length 0 or 1).

        Raises
        ------
        ValueError
            If `ontology_id` or `label` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not label:
            raise ValueError("label is required")

        endpoint = f"/api/search/{ontology_id}/exactLabel"
        params = {"label": label}

        logger.debug("Searching for exact label %r in ontology %r", label, ontology_id)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def get_classes_by_primary_id(
            self,
            class_primary_id: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
    ) -> dict:
        """
        Get classes whose *primary ID* exactly matches the supplied string.

        Parameters
        ----------
        class_primary_id : str
            The primary ID to get (required).
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.

        Returns
        -------
        dict
            JSON response from the endpoint.

        Raises
        ------
        ValueError
            If `class_primary_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not class_primary_id:
            raise ValueError("class_primary_id is required")

        endpoint = "/api/search/primaryId"
        params: dict[str, Union[str, list[str]]] = {"q": class_primary_id}

        if ontology_list:
            # Accept a single ontology or a list; requests will encode lists as repeated params
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)

        logger.debug("Primary ID search %r (ontologies=%r)", class_primary_id, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)  # will raise if raise_for_status=True
        return self.json_or_raise(resp)

    def get_root_entities(
            self,
            ontology_id: str,
            entity_type: str = "classes",
            from_: int = 0,
            size: int = 10,
            transaction_id: Optional[str] = None,
            childcount: bool = False,
            full_response: bool = False,
    ) -> Union[list[dict], dict]:
        """
        Retrieve root entities of a given type in an ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology ID (e.g., "efo").
        entity_type : {"classes","properties","instances"}, default "classes"
            Entity type to fetch roots for.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results to return.
        transaction_id : str, optional
            If provided, include uncommitted changes from this transaction.
        childcount : bool, default False
            Whether to include child-count information in results.
        full_response : bool, default False
            If True, return the full JSON response (with pagination metadata);
            otherwise return a list of entity dicts.

        Returns
        -------
        list[dict] | dict
            Root entity dicts (default) or full JSON if `full_response=True`.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `entity_type` is invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        allowed = {"classes", "properties", "instances"}
        if entity_type not in allowed:
            raise ValueError(f"entity_type must be one of {sorted(allowed)}")

        endpoint = f"/api/tree/{ontology_id}/{entity_type}/roots"
        params = {
            "from": from_,
            "size": size,
            "childcount": str(childcount).lower(),
        }
        if transaction_id:
            params["transactionId"] = transaction_id

        logger.debug("Fetching root %s from ontology %r (from=%d, size=%d, childcount=%s)",
                     entity_type, ontology_id, from_, size, childcount)

        resp = self.request("GET", endpoint, params=params)
        data = self.json_or_raise(resp)

        if full_response:
            return data
        return [el.get("value", el) for el in data.get("elements", [])]

    def get_paths_from_root(
            self,
            ontology_id: str,
            class_primary_id: str,
            children_relation_max_size: int = 50,
            maximum_number_of_paths: int = 100,
            *,
            as_: str = "ids",  # 'ids' | 'labels' | 'objects'
            include_fake_root: bool = False,
    ) -> list[list[Union[str, dict]]]:
        """
        Return paths from the synthetic 'THING' root to a class.

        Parameters
        ----------
        ontology_id : str
            Ontology ID (e.g., "efo").
        class_primary_id : str
            Primary ID of the target class (e.g., "http://www.ebi.ac.uk/efo/EFO_0000001" or "EFO_0000001").
        children_relation_max_size : int, default 50
            Limit breadth when exploring children.
        maximum_number_of_paths : int, default 100
            Maximum number of distinct paths to return.
        as_ : {'ids','labels','objects'}, default 'ids'
            Shape of each path segment:
              - 'ids'    → use `value.primaryID`.
              - 'labels' → use `value.primaryLabel`.
              - 'objects'→ return the raw `value` dicts.
        include_fake_root : bool, default False
            If False, drop the synthetic 'THING' node from returned paths.

        Returns
        -------
        list[list[Union[str, dict]]]
            A list of root→…→target paths. Each path is a list in the order encountered.

        Raises
        ------
        ValueError
            If required parameters are missing.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not class_primary_id:
            raise ValueError("class_primary_id is required")
        if as_ not in {"ids", "labels", "objects"}:
            raise ValueError("as_ must be one of {'ids','labels','objects'}")

        endpoint = f"/api/ontologies/{ontology_id}/classes/paths-from-root"
        params = {
            "classPrimaryId": class_primary_id,
            "childrenRelationMaxSize": int(children_relation_max_size),
            "maximumNumberOfPaths": int(maximum_number_of_paths),
        }

        resp = self.request("GET", endpoint, params=params)
        tree = self.json_or_raise(resp)  # shape: {"value": {...}, "leaves": [...]}

        def pick(v: Optional[dict], as_: str) -> Optional[Union[str, dict]]:
            if not isinstance(v, dict):  # value may be None
                return None
            if as_ == "objects":
                return v
            if as_ == "labels":
                return v.get("primaryLabel")
            # default 'ids'
            return v.get("primaryID")

        paths: list[list[Union[str, dict]]] = []

        def dfs(node: dict, acc: list[Union[str, dict]]) -> None:
            # Some server versions can return nodes with value=None
            value = node.get("value")
            leaves = node.get("leaves") or []

            added = False
            picked = pick(value, as_)
            if picked is not None:
                acc.append(picked)
                added = True

            if not leaves:
                # Only record a path if we actually added a node
                if added:
                    paths.append(acc.copy())
            else:
                for child in leaves:
                    if isinstance(child, dict):
                        dfs(child, acc)

            if added:
                acc.pop()

        dfs(tree, [])

        if not include_fake_root and paths:
            # drop the first hop (synthetic 'THING') if it’s present
            def drop_fake(p: list[Union[str, dict]]) -> list[Union[str, dict]]:
                return p[1:] if len(p) and (
                            p[0] == "THING" or (isinstance(p[0], dict) and p[0].get("primaryID") == "THING")) else p

            paths = [drop_fake(p) for p in paths]

        return paths
