"""Tiferet Monday Document Models"""

# *** imports

# ** infra
from tiferet import (
    ModelObject,
    StringType,
    ListType,
    ModelType,
)

# *** models

# * model: document_block
class DocumentBlock(ModelObject):
    """
    Represents a block of content within a document.
    """

    # * attribute: id
    id = StringType(
        required=True,
        metadata=dict(
            description='The unique identifier of the document block.'
        )
    )

    # * attribute: type
    type = StringType(
        default='text',
        metadata=dict(
            description='The type of the document block (e.g., text, image, etc.).'
        )
    )

    # * attribute: content
    content = StringType(
        default='',
        metadata=dict(
            description='The content of the document block.'
        )
    )

# ** model: document
class Document(ModelObject):
    """
    Represents a document in the system.
    """

    # * attribute: id
    id = StringType(
        required=True,
        metadata=dict(
            description='The unique identifier of the document.'
        )
    )

    # * attribute: name
    name = StringType(
        required=True,
        metadata=dict(
            description='The name of the document.'
        )
    )

    # * attribute: object_id
    object_id = StringType(
        required=True,
        metadata=dict(
            description='The identifier of the object associated with the document.'
        )
    )

    # * attribute: blocks
    blocks = ListType(
        ModelType(DocumentBlock),
        default=[],
        metadata=dict(
            description='A list of blocks within the document.'
        )
    )