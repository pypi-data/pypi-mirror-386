"""Tiferet Monday Document Data Objects"""

# *** imports

# ** infra
from tiferet import DataObject

# ** app
from ..models import Document

# *** data

# ** data: document_data
class DocumentData(DataObject, Document):
    """
    Represents a document in the Tiferet Monday application.
    """

    class Options():
        """
        Options for the DocumentData class.
        """
        serialize_when_none = False
        roles = dict(
            to_model=DataObject.deny('blocks'),
            to_data=DataObject.deny('blocks')
        )

    # * method: to_primitive
    def to_primitive(self, role = 'to_data', **kwargs) -> dict:
        """
        Converts the DocumentData instance to a primitive dictionary representation.

        :param role: The role to use for serialization.
        :type role: str
        :param kwargs: Additional keyword arguments.
        :return: A dictionary representation of the DocumentData instance.
        :rtype: dict
        """
        
        # Call the parent method to get the primitive representation.
        return dict(
            **super().to_primitive(role=role, **kwargs),
            blocks=[block.to_primitive() for block in self.blocks]
        )

    # * method: map
    def map(self) -> Document:
        """
        Maps the DocumentData instance to a DocumentContract.

        :return: The mapped DocumentContract instance.
        :rtype: DocumentContract
        """
        
        return super().map(Document)