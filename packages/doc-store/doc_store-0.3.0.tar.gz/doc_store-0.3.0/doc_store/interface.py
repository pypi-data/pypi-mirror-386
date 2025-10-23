import io
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, Literal, TypeVar

from PIL import Image
from pydantic import BaseModel

from .io import read_file, read_image
from .pdf_doc import PDFDocument
from .s3 import head_s3_object, put_s3_object
from .utils import BlockingThreadPool, secs_to_readable

#########
# Input #
#########


class InputModel(BaseModel):
    pass


class MetricInput(InputModel):
    value: float | int


class ValueInput(InputModel):
    value: Any


class TaskInput(InputModel):
    command: str
    args: dict[str, Any] | None = None


class DocInput(InputModel):
    pdf_path: str
    pdf_filename: str | None = None
    orig_path: str | None = None
    orig_filename: str | None = None
    tags: list[str] | None = None


class PageInput(InputModel):
    image_path: str
    image_dpi: int | None = None
    doc_id: str | None = None
    page_idx: int | None = None
    tags: list[str] | None = None


class DocPageInput(InputModel):
    image_path: str
    image_dpi: int | None = None
    tags: list[str] | None = None


class BlockInput(InputModel):
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None
    # TODO: score?
    tags: list[str] | None = None


class LayoutInput(InputModel):
    blocks: list[BlockInput]
    relations: list[dict] | None = None
    tags: list[str] | None = None


class ContentInput(InputModel):
    format: str
    content: str
    tags: list[str] | None = None


class ContentBlockInput(InputModel):
    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None
    content: str | None = None
    format: str | None = None
    score: float | None = None
    block_tags: list[str] | None = None
    content_tags: list[str] | None = None


class GrabbedTaskInput(InputModel):
    id: str
    grab_time: int


##########
# Output #
##########


class Element(BaseModel):
    """Base class for all elements."""

    id: str
    rid: int
    create_time: int | None = None
    update_time: int | None = None
    _store: "DocStoreInterface | None" = None

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        state.pop("_store", None)
        return state

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)

    @property
    def store(self) -> "DocStoreInterface":
        """Get the store associated with this element."""
        if not self._store:
            raise ValueError("Element does not have a store.")
        return self._store

    @store.setter
    def store(self, store: "DocStoreInterface") -> None:
        """Set the store for this element."""
        if not isinstance(store, DocStoreInterface):
            raise TypeError("store must be an instance of DocStoreInterface.")
        self._store = store


class DocElement(Element):
    """Base class for all doc elements."""

    tags: list[str] = []
    metrics: dict = {}

    def add_tag(self, tag: str) -> None:
        """Add tag to an element."""
        self.store.add_tag(self.id, tag)
        if tag not in self.tags:
            self.tags = self.tags + [tag]

    def del_tag(self, tag: str) -> None:
        """Delete tag from an element."""
        self.store.del_tag(self.id, tag)
        if tag in self.tags:
            self.tags = [t for t in self.tags if t != tag]

    def add_metric(self, name: str, metric_input: MetricInput) -> None:
        """Add metric to an element."""
        self.store.add_metric(self.id, name, metric_input)
        self.metrics = {**self.metrics, name: metric_input.value}

    def del_metric(self, name: str) -> None:
        """Delete metric from an element."""
        self.store.del_metric(self.id, name)
        self.metrics = {k: v for k, v in self.metrics.items() if k != name}

    def try_get_value(self, key: str) -> "Value | None":
        """Try to get a value by key."""
        return self.store.try_get_value_by_elem_id_and_key(self.id, key)

    def get_value(self, key: str) -> "Value":
        """Get a value by key."""
        return self.store.get_value_by_elem_id_and_key(self.id, key)

    def find_values(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Value"]:
        """Find all values of the element."""
        return self.store.find_values(
            query=query,
            elem_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_value(self, key: str, value_input: ValueInput) -> "Value":
        """Insert a value for the element."""
        return self.store.insert_value(self.id, key, value_input)

    def find_tasks(
        self,
        query: dict | None = None,
        command: str | None = None,
        status: str | None = None,
        create_user: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Task"]:
        """List tasks of the element by filters."""
        return self.store.find_tasks(
            query=query,
            target=self.id,
            command=command,
            status=status,
            create_user=create_user,
            skip=skip,
            limit=limit,
        )

    def insert_task(self, task_input: TaskInput) -> "Task":
        """Insert a task for the element."""
        return self.store.insert_task(self.id, task_input)


class Doc(DocElement):
    """Doc in the store."""

    pdf_path: str
    pdf_filename: str | None = None
    pdf_filesize: int
    pdf_hash: str
    num_pages: int
    page_width: float
    page_height: float
    metadata: dict = {}

    # Original file info (if exists)
    orig_path: str | None = None
    orig_filesize: int | None = None
    orig_filename: str | None = None
    orig_hash: str | None = None

    @property
    def pdf_bytes(self) -> bytes:
        """Get the PDF bytes of the doc."""
        return read_file(self.pdf_path)

    @property
    def pdf(self) -> PDFDocument:
        """Get the PDF document associated with the doc."""
        return PDFDocument(self.pdf_bytes)

    @property
    def pages(self) -> list["Page"]:
        """Get all pages of the doc."""
        pages = list(self.find_pages())
        pages.sort(key=lambda p: p.page_idx or 0)
        return pages

    def find_pages(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Page"]:
        """List pages of the doc by filters."""
        return self.store.find_pages(
            query=query,
            doc_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_page(self, page_idx: int, page_input: DocPageInput) -> "Page":
        """Insert a page for the doc, return the inserted page."""
        return self.store.insert_page(
            PageInput(
                image_path=page_input.image_path,
                image_dpi=page_input.image_dpi,
                doc_id=self.id,
                page_idx=page_idx,
                tags=page_input.tags,
            )
        )


class Page(DocElement):
    """Page of a doc."""

    doc_id: str | None = None
    page_idx: int | None = None
    image_path: str
    image_filesize: int
    image_hash: str
    image_width: int
    image_height: int
    image_dpi: int | None = None

    @property
    def image_bytes(self) -> bytes:
        """Get the image bytes of the page."""
        return read_file(self.image_path)

    @property
    def image(self) -> Image.Image:
        """Get the image of the page."""
        return read_image(self.image_path)

    @property
    def image_pub_link(self) -> str:
        """Get the public link of the page image."""
        image_ext = self.image_path.split(".")[-1].lower()
        if image_ext in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif image_ext in ["png"]:
            mime_type = "image/png"
        else:
            raise ValueError(f"Unsupported image format: {image_ext}.")

        pub_path = f"ddp-pages/{self.id}.{image_ext}"
        pub_s3_path = f"s3://pub-link/{pub_path}"
        pub_link_url = f"https://pub-link.shlab.tech/{pub_path}"

        if not head_s3_object(pub_s3_path):
            put_s3_object(pub_s3_path, self.image_bytes, ContentType=mime_type)
        return pub_link_url

    @property
    def super_block(self) -> "Block":
        """Get the super block of the page."""
        return self.store.get_super_block(self.id)

    @property
    def doc(self) -> Doc | None:
        """Get the doc associated with the page."""
        return self.store.get_doc(self.doc_id) if self.doc_id else None

    def try_get_layout(self, provider: str) -> "Layout | None":
        """Try to get the layout of the page by provider."""
        return self.store.try_get_layout_by_page_id_and_provider(self.id, provider)

    def get_layout(self, provider: str) -> "Layout":
        """Get the layout of the page by provider."""
        return self.store.get_layout_by_page_id_and_provider(self.id, provider)

    def find_layouts(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Layout"]:
        """List layouts of the page by filters."""
        return self.store.find_layouts(
            query=query,
            page_id=self.id,
            skip=skip,
            limit=limit,
        )

    def find_blocks(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Block"]:
        """List blocks of the page by filters."""
        return self.store.find_blocks(
            query=query,
            page_id=self.id,
            skip=skip,
            limit=limit,
        )

    def find_contents(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Content"]:
        """List contents of the page by filters."""
        return self.store.find_contents(
            query=query,
            page_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_layout(self, provider: str, layout_input: LayoutInput, insert_blocks=True, upsert=False) -> "Layout":
        """Insert a layout for the page, return the inserted layout."""
        return self.store.insert_layout(self.id, provider, layout_input, insert_blocks, upsert)

    def upsert_layout(self, provider: str, layout_input: LayoutInput, insert_blocks=True) -> "Layout":
        """Upsert a layout for the page, return the inserted or updated layout."""
        return self.store.upsert_layout(self.id, provider, layout_input, insert_blocks)

    def insert_block(self, block_input: BlockInput) -> "Block":
        """Insert a block for the page, return the inserted block."""
        return self.store.insert_block(self.id, block_input)

    def insert_blocks(self, blocks: list[BlockInput]) -> list["Block"]:
        """Insert multiple blocks for the page, return the inserted blocks."""
        return self.store.insert_blocks(self.id, blocks)

    def insert_content_blocks_layout(
        self,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> "Layout":
        """Insert a layout with content blocks for the page."""
        return self.store.insert_content_blocks_layout(
            self.id,
            provider,
            content_blocks,
            upsert,
        )


class PageElement(DocElement):
    """Base class for elements that are associated with a page."""

    page_id: str

    @property
    def page(self) -> Page:
        """Get the page associated with this element."""
        return self.store.get_page(self.page_id)


class Layout(PageElement):
    """Layout of a page, containing blocks and relations."""

    provider: str
    blocks: list["Block"]
    relations: list[dict] = []

    def list_versions(self) -> list[str]:
        """List all content versions of the layout."""
        block_ids = [block.id for block in self.blocks]
        if not block_ids:
            return []

        versions = set()
        query = {"block_id": {"$in": block_ids}}
        for content in self.store.find_contents(query=query):
            versions.add(content.version)
        return sorted(versions)

    def list_contents(self, version: str) -> list["Content"]:
        """Get all contents of the layout by version."""
        if not version:
            raise ValueError("Version must be specified to get contents.")

        block_ids = [block.id for block in self.blocks]
        if not block_ids:
            return []

        query = {"block_id": {"$in": block_ids}, "version": version}
        return list(self.store.find_contents(query=query))


class Block(PageElement):
    """Block of a page, representing a specific area with a type."""

    type: str
    bbox: list[float]
    angle: Literal[None, 0, 90, 180, 270] = None

    @property
    def image(self) -> Image.Image:
        """Get the image of the block."""
        bbox = self.bbox
        angle = self.angle
        image = self.page.image

        x1, y1, x2, y2 = bbox
        x1 = x1 * image.width
        y1 = y1 * image.height
        x2 = x2 * image.width
        y2 = y2 * image.height

        image = image.crop((x1, y1, x2, y2))
        if angle:
            image = image.rotate(angle, expand=True)
        return image

    @property
    def image_bytes(self) -> bytes:
        """Get the image bytes of the block."""
        image = self.image
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            return output.getvalue()

    @property
    def image_pub_link(self) -> str:
        """Get the public link of the page image."""
        pub_path = f"ddp-blocks/{self.id}.png"
        pub_s3_path = f"s3://pub-link/{pub_path}"
        pub_link_url = f"https://pub-link.shlab.tech/{pub_path}"

        if not head_s3_object(pub_s3_path):
            put_s3_object(pub_s3_path, self.image_bytes, ContentType="image/png")
        return pub_link_url

    def try_get_content(self, version: str) -> "Content | None":
        """Try to get the content of the block by version."""
        return self.store.try_get_content_by_block_id_and_version(self.id, version)

    def get_content(self, version: str) -> "Content":
        """Get the content of the block by version."""
        return self.store.get_content_by_block_id_and_version(self.id, version)

    def find_contents(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable["Content"]:
        """List contents of the block by filters."""
        return self.store.find_contents(
            query=query,
            block_id=self.id,
            skip=skip,
            limit=limit,
        )

    def insert_content(self, version: str, content_input: ContentInput, upsert=False) -> "Content":
        """Insert content for the block, return the inserted content."""
        return self.store.insert_content(self.id, version, content_input, upsert)

    def upsert_content(self, version: str, content_input: ContentInput) -> "Content":
        """Upsert content for the block, return the inserted or updated content."""
        return self.store.upsert_content(self.id, version, content_input)


class Content(PageElement):
    """Content of a block, representing the text or data within a block."""

    block_id: str
    version: str
    format: str
    content: str

    @property
    def block(self) -> Block:
        """Get the block associated with this content."""
        return self.store.get_block(self.block_id)


class Value(Element):
    elem_id: str
    key: str
    type: str
    value: Any

    @property
    def elem(self) -> DocElement:
        """Get the element associated with this value."""
        return self.store.get(self.elem_id)


class Task(GrabbedTaskInput, Element):
    target: str  # TODO: change
    command: str
    args: dict[str, Any] = {}
    status: str
    create_user: str
    update_user: str | None = None
    grab_user: str | None = None
    grab_time: int = 0
    error_message: str | None = None


class ElementNotFoundError(Exception):
    pass


class ElementExistsError(Exception):
    pass


class DocExistsError(ElementExistsError):
    def __init__(self, message: str, pdf_path: str, pdf_hash: str | None):
        super().__init__(message)
        self.pdf_path = pdf_path
        self.pdf_hash = pdf_hash


class TaskMismatchError(Exception):
    pass


ElemType = Literal["doc", "page", "layout", "block", "content", "value", "task"]

T = TypeVar("T", bound=Doc | Page | Layout | Block | Content | Value | Task)
Q = TypeVar("Q", bound=Doc | Page | Layout | Block | Content | Value | Task)


def _cls_to_elem_type(cls: type[T] | type[Q]) -> ElemType:
    return cls.__name__.lower()  # type: ignore


class DocStoreInterface(ABC):
    def get(self, elem_id: str) -> DocElement:
        """Get a element by its ID."""
        if elem_id.startswith("doc-"):
            return self.get_doc(elem_id)
        if elem_id.startswith("page-"):
            return self.get_page(elem_id)
        if elem_id.startswith("layout-"):
            return self.get_layout(elem_id)
        if elem_id.startswith("block-"):
            return self.get_block(elem_id)
        if elem_id.startswith("content-"):
            return self.get_content(elem_id)
        # fallback to block
        return self.get_block(elem_id)

    def try_get(self, elem_id: str) -> DocElement | None:
        """Try to get a element by its ID, return None if not found."""
        try:
            return self.get(elem_id)
        except ElementNotFoundError:
            return None

    def try_get_doc(self, doc_id: str) -> Doc | None:
        """Try to get a doc by its ID, return None if not found."""
        try:
            return self.get_doc(doc_id)
        except ElementNotFoundError:
            return None

    def try_get_doc_by_pdf_path(self, pdf_path: str) -> Doc | None:
        """Try to get a doc by its PDF path, return None if not found."""
        try:
            return self.get_doc_by_pdf_path(pdf_path)
        except ElementNotFoundError:
            return None

    def try_get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc | None:
        """Try to get a doc by its PDF sha256sum hex-string, return None if not found."""
        try:
            return self.get_doc_by_pdf_hash(pdf_hash)
        except ElementNotFoundError:
            return None

    def try_get_page(self, page_id: str) -> Page | None:
        """Try to get a page by its ID, return None if not found."""
        try:
            return self.get_page(page_id)
        except ElementNotFoundError:
            return None

    def try_get_page_by_image_path(self, image_path: str) -> Page | None:
        """Try to get a page by its image path, return None if not found."""
        try:
            return self.get_page_by_image_path(image_path)
        except ElementNotFoundError:
            return None

    def try_get_layout(self, layout_id: str) -> Layout | None:
        """Try to get a layout by its ID, return None if not found."""
        try:
            return self.get_layout(layout_id)
        except ElementNotFoundError:
            return None

    def try_get_layout_by_page_id_and_provider(self, page_id: str, provider: str) -> Layout | None:
        """Try to get a layout by its page ID and provider, return None if not found."""
        try:
            return self.get_layout_by_page_id_and_provider(page_id, provider)
        except ElementNotFoundError:
            return None

    def try_get_block(self, block_id: str) -> Block | None:
        """Try to get a block by its ID, return None if not found."""
        try:
            return self.get_block(block_id)
        except ElementNotFoundError:
            return None

    def try_get_content(self, content_id: str) -> Content | None:
        """Try to get a content by its ID, return None if not found."""
        try:
            return self.get_content(content_id)
        except ElementNotFoundError:
            return None

    def try_get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content | None:
        """Try to get a content by its block ID and version, return None if not found."""
        try:
            return self.get_content_by_block_id_and_version(block_id, version)
        except ElementNotFoundError:
            return None

    def try_get_value(self, value_id: str) -> Value | None:
        """Try to get a value by its ID, return None if not found."""
        try:
            return self.get_value(value_id)
        except ElementNotFoundError:
            return None

    def try_get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value | None:
        """Try to get a value by its elem_id and key, return None if not found."""
        try:
            return self.get_value_by_elem_id_and_key(elem_id, key)
        except ElementNotFoundError:
            return None

    def try_get_task(self, task_id: str) -> Task | None:
        """Try to get a task by its ID, return None if not found."""
        try:
            return self.get_task(task_id)
        except ElementNotFoundError:
            return None

    def doc_tags(self) -> list[str]:
        """Get all distinct tags for docs."""
        return self.distinct_values("doc", "tags")

    def page_tags(self) -> list[str]:
        """Get all distinct tags for pages."""
        return self.distinct_values("page", "tags")

    def layout_providers(self) -> list[str]:
        """Get all distinct layout providers."""
        return self.distinct_values("layout", "provider")

    def layout_tags(self) -> list[str]:
        """Get all distinct tags for layouts."""
        return self.distinct_values("layout", "tags")

    def block_tags(self) -> list[str]:
        """Get all distinct tags for blocks."""
        return self.distinct_values("block", "tags")

    def content_versions(self) -> list[str]:
        """Get all distinct content versions."""
        return self.distinct_values("content", "version")

    def content_tags(self) -> list[str]:
        """Get all distinct tags for contents."""
        return self.distinct_values("content", "tags")

    def find_docs(
        self,
        query: dict | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Doc]:
        """List docs by filters."""
        query = query or {}
        return self.find("doc", query, skip=skip, limit=limit)  # type: ignore

    def find_pages(
        self,
        query: dict | None = None,
        doc_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Page]:
        """List pages by filters."""
        query = query or {}
        if doc_id is not None:
            query["doc_id"] = doc_id
        return self.find(Page, query, skip=skip, limit=limit)  # type: ignore

    def find_layouts(
        self,
        query: dict | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Layout]:
        """List layouts by filters."""
        query = query or {}
        if page_id is not None:
            query["page_id"] = page_id
        return self.find(Layout, query, skip=skip, limit=limit)  # type: ignore

    def find_blocks(
        self,
        query: dict | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Block]:
        """List blocks by filters."""
        query = query or {}
        if page_id is not None:
            query["page_id"] = page_id
        return self.find(Block, query, skip=skip, limit=limit)  # type: ignore

    def find_contents(
        self,
        query: dict | None = None,
        page_id: str | None = None,
        block_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Content]:
        """List contents by filters."""
        query = query or {}
        if page_id is not None:
            query["page_id"] = page_id
        if block_id is not None:
            query["block_id"] = block_id
        return self.find(Content, query, skip=skip, limit=limit)  # type: ignore

    def find_values(
        self,
        query: dict | None = None,
        elem_id: str | None = None,
        key: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Value]:
        """List values by filters."""
        query = query or {}
        if elem_id is not None:
            query["elem_id"] = elem_id
        if key is not None:
            query["key"] = key
        return self.find(Value, query, skip=skip, limit=limit)  # type: ignore

    def find_tasks(
        self,
        query: dict | None = None,
        target: str | None = None,
        command: str | None = None,
        status: str | None = None,
        create_user: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Task]:
        """List tasks by filters."""
        query = query or {}
        if target is not None:
            query["target"] = target
        if command is not None:
            query["command"] = command
        if status is not None:
            query["status"] = status
        if create_user is not None:
            query["create_user"] = create_user
        return self.find(Task, query, skip=skip, limit=limit)  # type: ignore

    def upsert_layout(self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=True) -> Layout:
        """Upsert a layout for a page."""
        return self.insert_layout(page_id, provider, layout_input, insert_blocks, upsert=True)

    def upsert_content(self, block_id: str, version: str, content_input: ContentInput) -> Content:
        """Upsert content for a block."""
        return self.insert_content(block_id, version, content_input, upsert=True)

    def grab_new_task(
        self,
        command: str,
        args: dict[str, Any] = {},
        create_user: str | None = None,
        hold_sec=3600,
    ) -> Task | None:
        """Grab a new task for processing."""
        grabbed_tasks = self.grab_new_tasks(
            command=command,
            args=args,
            create_user=create_user,
            num=1,
            hold_sec=hold_sec,
        )
        return grabbed_tasks[0] if grabbed_tasks else None

    def update_grabbed_task(
        self,
        task: GrabbedTaskInput,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
    ):
        """Update a task after processing."""
        return self.update_task(
            task_id=task.id,
            grab_time=task.grab_time,
            status=status,
            error_message=error_message,
        )

    def iterate(
        self,
        elem_type: type[T],
        func: Callable[[int, T], None],
        query: dict | list[dict] | None = None,
        query_from: type[Q] | None = None,
        max_workers: int = 10,
        total: int | None = None,
    ) -> None:
        if query is None:
            query = {}

        if total is None:
            print("Estimating element count...")
            begin = time.time()
            cnt = self.count(
                elem_type=_cls_to_elem_type(elem_type),
                query=query,
                query_from=_cls_to_elem_type(query_from) if query_from else None,
                estimated=True,
            )
            elapsed = round(time.time() - begin, 2)
            print(f"Estimation done. Found {cnt} elements in {elapsed} seconds.")
        else:
            cnt = max(0, total)

        print("Iterating over elements...")
        begin = time.time()
        cursor = self.find(
            elem_type=_cls_to_elem_type(elem_type),
            query=query,
            query_from=_cls_to_elem_type(query_from) if query_from else None,
        )

        last_report_time = time.time()
        with BlockingThreadPool(max_workers) as executor:
            for idx, elem_data in enumerate(cursor):
                now = time.time()
                if idx > 0 and (now - last_report_time) > 10:
                    curr = str(idx).rjust(len(str(cnt)))
                    curr = f"{curr}/{cnt}" if cnt > 0 else curr
                    elapsed = round(now - begin, 2)
                    rps = round(idx / elapsed, 2) if elapsed > 0 else idx
                    message = f"Processed {curr} elements in {elapsed}s, {rps}r/s"
                    if cnt > 0:
                        prog = round(idx / cnt * 100, 2)
                        remaining_secs = int(elapsed * (cnt - idx) / idx)
                        rtime = secs_to_readable(remaining_secs)
                        message = f"[{prog:5.2f}%] {message}, remaining time: {rtime}"
                    print(message)
                    last_report_time = now
                executor.submit(func, idx, elem_data)
            executor.shutdown(wait=True)

    @abstractmethod
    def get_doc(self, doc_id: str) -> Doc:
        """Get a doc by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_doc_by_pdf_path(self, pdf_path: str) -> Doc:
        """Get a doc by its PDF path."""
        raise NotImplementedError()

    @abstractmethod
    def get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc:
        """Get a doc by its PDF sha256sum hex-string."""
        raise NotImplementedError()

    @abstractmethod
    def get_page(self, page_id: str) -> Page:
        """Get a page by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_page_by_image_path(self, image_path: str) -> Page:
        """Get a page by its image path."""
        raise NotImplementedError()

    @abstractmethod
    def get_layout(self, layout_id: str) -> Layout:
        """Get a layout by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str) -> Layout:
        """Get a layout by its page ID and provider."""
        raise NotImplementedError()

    @abstractmethod
    def get_block(self, block_id: str) -> Block:
        """Get a block by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_super_block(self, page_id: str) -> Block:
        """Get the super block for a page."""
        raise NotImplementedError()

    @abstractmethod
    def get_content(self, content_id: str) -> Content:
        """Get a content by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content:
        """Get a content by its block ID and version."""
        raise NotImplementedError()

    @abstractmethod
    def get_value(self, value_id: str) -> Value:
        """Get a value by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value:
        """Get a value by its elem_id and key."""
        raise NotImplementedError()

    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        raise NotImplementedError()

    @abstractmethod
    def distinct_values(
        self,
        elem_type: ElemType,
        field: Literal["tags", "provider", "version"],
        query: dict | None = None,
    ) -> list[str]:
        """Get all distinct values for a specific field of an element type."""
        raise NotImplementedError()

    @abstractmethod
    def find(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[Element]:
        """Find elements of a specific type matching the query."""
        raise NotImplementedError()

    @abstractmethod
    def count(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        estimated: bool = False,
    ) -> int:
        """Count elements of a specific type matching the query."""
        raise NotImplementedError()

    ####################
    # WRITE OPERATIONS #
    ####################

    @abstractmethod
    def add_tag(self, elem_id: str, tag: str) -> None:
        """Add tag to an element."""
        raise NotImplementedError()

    @abstractmethod
    def del_tag(self, elem_id: str, tag: str) -> None:
        """Delete tag from an element."""
        raise NotImplementedError()

    @abstractmethod
    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput) -> None:
        """Add a metric to an element."""
        raise NotImplementedError()

    @abstractmethod
    def del_metric(self, elem_id: str, name: str) -> None:
        """Delete a metric from an element."""
        raise NotImplementedError()

    @abstractmethod
    def insert_value(self, elem_id: str, key: str, value_input: ValueInput) -> Value:
        """Insert a new value for a element."""
        raise NotImplementedError()

    @abstractmethod
    def insert_task(self, target_id: str, task_input: TaskInput) -> Task:
        """Insert a new task into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_doc(self, doc_input: DocInput, skip_ext_check=False) -> Doc:
        """Insert a new doc into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_page(self, page_input: PageInput) -> Page:
        """Insert a new page into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_layout(self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=True, upsert=False) -> Layout:
        """Insert a new layout into the database."""
        raise NotImplementedError()

    @abstractmethod
    def insert_block(self, page_id: str, block_input: BlockInput) -> Block:
        """Insert a new block for a page."""
        raise NotImplementedError()

    @abstractmethod
    def insert_blocks(self, page_id: str, blocks: list[BlockInput]) -> list[Block]:
        """Insert multiple blocks for a page."""
        raise NotImplementedError()

    @abstractmethod
    def insert_content(self, block_id: str, version: str, content_input: ContentInput, upsert=False) -> Content:
        """Insert a new content for a block."""
        raise NotImplementedError()

    @abstractmethod
    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> Layout:
        """Import content blocks and create a layout for a page."""
        raise NotImplementedError()

    ###################
    # TASK OPERATIONS #
    ###################

    @abstractmethod
    def grab_new_tasks(
        self,
        command: str,
        args: dict[str, Any] = {},
        create_user: str | None = None,
        num=10,
        hold_sec=3600,
    ) -> list[Task]:
        """Grab new tasks for processing."""
        raise NotImplementedError()

    @abstractmethod
    def update_task(
        self,
        task_id: str,
        grab_time: int,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
    ):
        """Update a task after processing."""
        raise NotImplementedError()
