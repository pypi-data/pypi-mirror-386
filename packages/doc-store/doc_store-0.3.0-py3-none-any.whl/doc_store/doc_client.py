import json
from typing import Any, Iterable, Literal

import httpx

from .config import config
from .interface import (
    Block,
    BlockInput,
    Content,
    ContentBlockInput,
    ContentInput,
    Doc,
    DocInput,
    DocStoreInterface,
    Element,
    ElementExistsError,
    ElementNotFoundError,
    ElemType,
    InputModel,
    Layout,
    LayoutInput,
    MetricInput,
    Page,
    PageInput,
    T,
    Task,
    TaskInput,
    Value,
    ValueInput,
)
from .utils import get_username


class DocClient(DocStoreInterface):
    """HTTP client for DocStore API."""

    def __init__(
        self,
        server_url: str | None = None,
        prefix: str = "/api/v1",
        timeout: int = 300,
        connect_timeout: int = 30,
    ):
        """
        Initialize DocClient.

        Args:
            server_url: Base URL of the DocStore API server
            timeout: Read timeout in seconds (for stream requests, this is per-chunk)
            connect_timeout: Connection timeout in seconds
        """
        super().__init__()

        if not server_url:
            server_url = config.server.url
        if not server_url:
            raise ValueError("server_url must be provided either in argument or config.")
        self.server_url = server_url.rstrip("/")
        self.prefix = prefix.rstrip("/")

        self.client = httpx.Client(
            headers={
                "X-Username": get_username(),
            },
            timeout=httpx.Timeout(
                connect=connect_timeout,
                read=timeout,
                write=timeout,
                pool=connect_timeout,
            ),
        )

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        json_data: dict | list | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        """Make HTTP request to the server."""
        url = f"{self.server_url}{self.prefix}{path}"

        response = self.client.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
        )

        if response.status_code == 400:
            error_data = response.json()
            raise ValueError(error_data.get("message", "Bad request"))
        elif response.status_code == 403:
            error_data = response.json()
            raise PermissionError(error_data.get("message", "Permission denied"))
        elif response.status_code == 404:
            error_data = response.json()
            raise ElementNotFoundError(error_data.get("message", "Element not found"))
        elif response.status_code == 409:
            error_data = response.json()
            raise ElementExistsError(error_data.get("message", "Element already exists"))
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                raise Exception(error_data.get("message", f"HTTP {response.status_code}"))
            except (ValueError, KeyError):
                response.raise_for_status()

        return response

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Make GET request and return JSON response."""
        response = self._request("GET", path, params=params)
        return response.json()

    def _post(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> dict | list:
        """Make POST request and return JSON response."""
        response = self._request("POST", path, json_data=json_data, params=params)
        return response.json()

    def _put(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> dict | None:
        """Make PUT request and return JSON response."""
        response = self._request("PUT", path, json_data=json_data, params=params)
        if response.status_code == 204 or len(response.content) == 0:
            return None
        return response.json()

    def _delete(self, path: str) -> dict | None:
        """Make DELETE request and return JSON response."""
        response = self._request("DELETE", path)
        if response.status_code == 204 or len(response.content) == 0:
            return None
        return response.json()

    def _stream(self, path: str, json_data: dict | list | None = None, params: dict | None = None) -> Iterable[dict]:
        """Make POST request and stream JSON lines response."""
        url = f"{self.server_url}{self.prefix}{path}"

        with self.client.stream("POST", url, json=json_data, params=params) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    def _dump_elem(self, elem_input: InputModel) -> dict:
        """Dump element input model to dict for JSON serialization."""
        if isinstance(elem_input, LayoutInput):
            return {
                "blocks": [self._dump_elem(b) for b in elem_input.blocks],
                "relations": elem_input.relations,
                "tags": elem_input.tags,
            }
        return elem_input.model_dump()

    def _parse_elem(self, elem_type: type[T], elem_data: dict) -> T:
        """Parse element data into the specified type."""
        if elem_type == Layout:
            blocks = elem_data.get("blocks") or []
            elem_data["blocks"] = [self._parse_elem(Block, b) for b in blocks]
        elem_object = elem_type(**elem_data)
        elem_object.store = self
        return elem_object

    ####################
    # READ OPERATIONS  #
    ####################

    def get_doc(self, doc_id: str) -> Doc:
        """Get a doc by its ID."""
        data = self._get(f"/docs/{doc_id}")
        return self._parse_elem(Doc, data)

    def get_doc_by_pdf_path(self, pdf_path: str) -> Doc:
        """Get a doc by its PDF path."""
        data = self._get(f"/docs/pdf-path/{pdf_path}")
        return self._parse_elem(Doc, data)

    def get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc:
        """Get a doc by its PDF sha256sum hex-string."""
        data = self._get(f"/docs/pdf-hash/{pdf_hash}")
        return self._parse_elem(Doc, data)

    def get_page(self, page_id: str) -> Page:
        """Get a page by its ID."""
        data = self._get(f"/pages/{page_id}")
        return self._parse_elem(Page, data)

    def get_page_by_image_path(self, image_path: str) -> Page:
        """Get a page by its image path."""
        data = self._get(f"/pages/image-path/{image_path}")
        return self._parse_elem(Page, data)

    def get_layout(self, layout_id: str) -> Layout:
        """Get a layout by its ID."""
        data = self._get(f"/layouts/{layout_id}")
        return self._parse_elem(Layout, data)

    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str) -> Layout:
        """Get a layout by its page ID and provider."""
        data = self._get(f"/pages/{page_id}/layouts/{provider}")
        return self._parse_elem(Layout, data)

    def get_block(self, block_id: str) -> Block:
        """Get a block by its ID."""
        data = self._get(f"/blocks/{block_id}")
        return self._parse_elem(Block, data)

    def get_super_block(self, page_id: str) -> Block:
        """Get the super block for a page."""
        data = self._get(f"/pages/{page_id}/super-block")
        return self._parse_elem(Block, data)

    def get_content(self, content_id: str) -> Content:
        """Get a content by its ID."""
        data = self._get(f"/contents/{content_id}")
        return self._parse_elem(Content, data)

    def get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content:
        """Get a content by its block ID and version."""
        data = self._get(f"/blocks/{block_id}/contents/{version}")
        return self._parse_elem(Content, data)

    def get_value(self, value_id: str) -> Value:
        """Get a value by its ID."""
        data = self._get(f"/values/{value_id}")
        return self._parse_elem(Value, data)

    def get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value:
        """Get a value by its elem_id and key."""
        data = self._get(f"/elements/{elem_id}/values/{key}")
        return self._parse_elem(Value, data)

    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        data = self._get(f"/tasks/{task_id}")
        return self._parse_elem(Task, data)

    def distinct_values(
        self,
        elem_type: ElemType,
        field: Literal["tags", "provider", "version"],
        query: dict | None = None,
    ) -> list[str]:
        """Get all distinct values for a specific field of an element type."""
        data = self._post(f"/distinct/{elem_type}/{field}", json_data=query)
        assert isinstance(data, list)
        return data

    def find(
        self,
        elem_type: ElemType | type,
        query: dict | list[dict] | None = None,
        query_from: ElemType | type | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Element]:
        """Find elements of a specific type matching the query."""
        # Convert class types to elem_type strings
        if isinstance(elem_type, type):
            elem_type = elem_type.__name__.lower()  # type: ignore
        if isinstance(query_from, type):
            query_from = query_from.__name__.lower()  # type: ignore

        params = {}
        if query_from:
            params["query_from"] = query_from
        if skip is not None:
            params["skip"] = skip
        if limit is not None:
            params["limit"] = limit

        # Map elem_type to element class
        elem_classes = {
            "doc": Doc,
            "page": Page,
            "layout": Layout,
            "block": Block,
            "content": Content,
            "value": Value,
            "task": Task,
        }

        assert isinstance(elem_type, str)
        elem_cls = elem_classes.get(elem_type, Element)

        for data in self._stream(f"/stream/{elem_type}", json_data=query, params=params):
            yield self._parse_elem(elem_cls, data)

    def count(
        self,
        elem_type: ElemType | type,
        query: dict | list[dict] | None = None,
        query_from: ElemType | type | None = None,
        estimated: bool = False,
    ) -> int:
        """Count elements of a specific type matching the query."""
        # Convert class types to elem_type strings
        if isinstance(elem_type, type):
            elem_type = elem_type.__name__.lower()  # type: ignore
        if isinstance(query_from, type):
            query_from = query_from.__name__.lower()  # type: ignore

        params = {}
        if query_from:
            params["query_from"] = query_from
        if estimated:
            params["estimated"] = estimated

        data = self._post(f"/count/{elem_type}", json_data=query, params=params)
        assert isinstance(data, int)
        return data

    ####################
    # WRITE OPERATIONS #
    ####################

    def add_tag(self, elem_id: str, tag: str) -> None:
        """Add tag to an element."""
        self._put(f"/elements/{elem_id}/tags/{tag}")

    def del_tag(self, elem_id: str, tag: str) -> None:
        """Delete tag from an element."""
        self._delete(f"/elements/{elem_id}/tags/{tag}")

    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput) -> None:
        """Add a metric to an element."""
        input_data = self._dump_elem(metric_input)
        self._put(f"/elements/{elem_id}/metrics/{name}", json_data=input_data)

    def del_metric(self, elem_id: str, name: str) -> None:
        """Delete a metric from an element."""
        self._delete(f"/elements/{elem_id}/metrics/{name}")

    def insert_value(self, elem_id: str, key: str, value_input: ValueInput) -> Value:
        """Insert a new value for a element."""
        input_data = self._dump_elem(value_input)
        data = self._put(f"/elements/{elem_id}/values/{key}", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Value, data)

    def insert_task(self, target_id: str, task_input: TaskInput) -> Task:
        """Insert a new task into the database."""
        input_data = self._dump_elem(task_input)
        data = self._post(f"/elements/{target_id}/tasks", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Task, data)

    def insert_doc(self, doc_input: DocInput, skip_ext_check=False) -> Doc:
        """Insert a new doc into the database."""
        input_data = self._dump_elem(doc_input)
        data = self._post("/docs", json_data=input_data, params={"skip_ext_check": skip_ext_check})
        assert isinstance(data, dict)
        return self._parse_elem(Doc, data)

    def insert_page(self, page_input: PageInput) -> Page:
        """Insert a new page into the database."""
        input_data = self._dump_elem(page_input)
        data = self._post("/pages", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Page, data)

    def insert_layout(self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=True, upsert=False) -> Layout:
        """Insert a new layout into the database."""
        input_data = self._dump_elem(layout_input)
        data = self._put(
            f"/pages/{page_id}/layouts/{provider}",
            json_data=input_data,
            params={"insert_blocks": insert_blocks, "upsert": upsert},
        )
        assert isinstance(data, dict)
        return self._parse_elem(Layout, data)

    def insert_block(self, page_id: str, block_input: BlockInput) -> Block:
        """Insert a new block for a page."""
        input_data = self._dump_elem(block_input)
        data = self._post(f"/pages/{page_id}/blocks", json_data=input_data)
        assert isinstance(data, dict)
        return self._parse_elem(Block, data)

    def insert_blocks(self, page_id: str, blocks: list[BlockInput]) -> list[Block]:
        """Insert multiple blocks for a page."""
        input_data = [self._dump_elem(b) for b in blocks]
        data = self._post(f"/pages/{page_id}/blocks/batch", json_data=input_data)
        assert isinstance(data, list)
        return [self._parse_elem(Block, block_data) for block_data in data]

    def insert_content(self, block_id: str, version: str, content_input: ContentInput, upsert=False) -> Content:
        """Insert a new content for a block."""
        input_data = self._dump_elem(content_input)
        data = self._put(
            f"/blocks/{block_id}/contents/{version}",
            json_data=input_data,
            params={"upsert": upsert},
        )
        assert isinstance(data, dict)
        return self._parse_elem(Content, data)

    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> Layout:
        """Import content blocks and create a layout for a page."""
        input_data = [self._dump_elem(b) for b in content_blocks]
        data = self._put(
            f"/pages/{page_id}/content-blocks-layouts/{provider}",
            json_data=input_data,
            params={"upsert": upsert},
        )
        assert isinstance(data, dict)
        return self._parse_elem(Layout, data)

    ###################
    # TASK OPERATIONS #
    ###################

    def grab_new_tasks(
        self,
        command: str,
        args: dict[str, Any] = {},
        create_user: str | None = None,
        num=10,
        hold_sec=3600,
    ) -> list[Task]:
        """Grab new tasks for processing."""
        params = {}
        if create_user:
            params["create_user"] = create_user
        params["num"] = num
        params["hold_sec"] = hold_sec
        data = self._post(f"/grab-new-tasks/{command}", json_data=args, params=params)
        return [self._parse_elem(Task, task_data) for task_data in data]

    def update_task(
        self,
        task_id: str,
        grab_time: int,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
    ):
        """Update a task after processing."""
        params = {}
        params["grab_time"] = grab_time
        params["status"] = status
        if error_message:
            params["error_message"] = error_message
        return self._post(f"/update-grabbed-task/{task_id}", params=params)
