import logging

from django.utils.translation import gettext_lazy as _

from celery import shared_task
from papermerge.core.ocr.document import ocr_document

from .models import (
    BaseTreeNode,
    Document,
    DocumentVersion,
    Folder,
    Page
)

logger = logging.getLogger(__name__)


@shared_task
def ocr_document_task(
    document_id,
    lang,
    namespace=None
):
    """
    OCR whole document, updates document's version and its `text` field
    """

    doc = Document.objects.get(pk=document_id)
    user_id = doc.user.id
    doc_version = doc.versions.last()

    ocr_document(
        user_id=user_id,
        document_id=document_id,
        file_name=doc_version.file_name,
        lang=lang,
        namespace=namespace,
        version=doc_version.number,
        target_version=doc_version.number + 1
    )
    # get document model
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist as exception:
        logger.error(exception, exc_info=True)
        return False

    new_doc_version = DocumentVersion(
        document=doc,
        number=doc_version.number + 1,
        file_name=doc_version.file_name,
        size=0,  # TODO: set to newly created file size
        page_count=doc_version.page_count,
        lang=lang,
        short_description=_("with OCRed text layer")
    )
    new_doc_version.save()

    for page_number in range(1, new_doc_version.page_count + 1):
        Page.objects.create(
            document_version=new_doc_version,
            number=page_number,
            page_count=new_doc_version.page_count,
            lang=lang
        )

    # update document text field (i.e so that document will be searchable)
    # doc.update_text_field()

    return True


@shared_task()
def nodes_move(
    source_parent,  # noqa
    target_parent,
    nodes
):
    """
    `source_parent` dictionary with only one key - 'id'
    `target_parent` dictionary with only one key - 'id'
    `nodes` is a list of {'id': <id>}. Example:
        [{'id': 1, 'id': 2}, {'id': 3}]

    Note that `source_parent` is not actually used. `source_parent`
    is part of the task, useful only in frontend part.
    """
    try:
        target_model = BaseTreeNode.objects.get(pk=target_parent['id'])
    except BaseTreeNode.DoesNotExist as exc:
        logger.error(exc, exc_info=True)
        return

    for node in nodes:
        try:
            node_model = BaseTreeNode.objects.get(pk=node['id'])
        except BaseTreeNode.DoesNotExist as exc:
            logger.error(exc, exc_info=True)

        node_model.refresh_from_db()   # this may take a while
        target_model.refresh_from_db()  # may take a while
        Document.objects.move_node(node_model, target_model)


def norm_pages_from_doc(document):
    logger.debug(f"Normalizing document {document.id}")
    for page in Page.objects.filter(document=document):
        page.norm()


def norm_pages_from_folder(folder):
    for descendent in folder.get_descendants():
        if isinstance(descendent, Document):
            norm_pages_from_doc(descendent)
        elif isinstance(descendent, Folder):
            norm_pages_from_folder(descendent)
        else:
            raise ValueError("Unexpected value for descendent instance")


@shared_task
def normalize_pages(origin):
    """
    Normalize Pages. The normalization was triggered model origin.
    origin can be either a Folder or a Document
    """
    if isinstance(origin, Document):
        norm_pages_from_doc(origin)
    elif isinstance(origin, Folder):
        norm_pages_from_folder(origin)
