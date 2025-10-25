"""Tiferet Monday Item Data Transfer Objects"""

# *** imports

# ** infra
from tiferet import (
    DataObject,
    ModelType,
    StringType,
    ListType,
)

# ** app
from ..models import (
    Item,
    ItemDetail
)
from ..contracts import (
    ItemContract,
    ItemDetailContract
)
from .column_value import (
    ColumnValueData
)

# *** data
        
# ** data: item_board_data
class ItemBoardData(DataObject):
    """
    Represents the data required to create an item in a Monday.com board.
    """

    class Options():
        """
        Options for the ItemBoardData class.
        """
        serialize_when_none = False
        roles = dict(
            to_model=DataObject.deny('id'),
            to_data=DataObject.allow()
        )

    # * attribute: id
    id = StringType(
        required=True,
        metadata=dict(
            description='The unique identifier of the board to which the item belongs.'
        )
    )

# ** data: item_group_data
class ItemGroupData(DataObject):
    """
    Represents the data required to create an item group in a Monday.com board.
    """

    class Options():
        """
        Options for the ItemGroupData class.
        """
        serialize_when_none = False
        roles = dict(
            to_model=DataObject.deny('id'),
            to_data=DataObject.allow()
        )

    # * attribute: id
    id = StringType(
        required=True,
        metadata=dict(
            description='The unique identifier of the group to which the item belongs.'
        )
    )

# ** data: item_data
class ItemData(DataObject, Item):
    """
    Represents the data required to create an item in a Monday.com board.
    """

    class Options():
        """
        Options for the ItemData class.
        """
        serialize_when_none = False
        roles = {
            'to_data': DataObject.deny('updates'),
            'to_model': DataObject.deny('board', 'updates')
        }

    # * attribute: board
    board = ModelType(
        ItemBoardData,
        required=True,
        metadata=dict(
            description='The board to which the item belongs.'
        )
    )

    # * method: to_primitive
    def to_primitive(self, role: str = 'to_data', **kwargs) -> dict:
        """
        Converts the data object to a primitive dictionary representation.

        :param role: The role to use for serialization.
        :type role: str
        :return: A dictionary representation of the data object.
        :rtype: dict
        """
        
        # Convert the data object to a primitive dictionary using the specified role.
        return dict(
            super().to_primitive(role=role, **kwargs),
            updates=[update.to_primitive() for update in self.updates],
        )

    # * method: map
    def map(self) -> ItemContract:
        """
        Maps the data object to an Item model.
        
        :return: An Item model instance.
        :rtype: ItemContract
        """
        
        # Map the board data to the Item model.
        return super().map(
            Item,
            board_id=self.board.id
        )
    
# ** data: item_detail_data
class ItemDetailData(DataObject, ItemDetail):
    """
    Represents the detailed data of an item in a Monday.com board.
    """

    class Options():
        """
        Options for the ItemDetailData class.
        """
        serialize_when_none = False
        roles = dict(
            to_model=DataObject.deny('board', 'group', 'parent_item', 'description', 'column_values'),
            to_data=DataObject.deny('description')
        )

    # * attribute: board
    board = ModelType(
        ItemBoardData,
        required=True,
        metadata=dict(
            description='The board to which the item belongs.'
        )
    )

    # * attribute: group
    group = ModelType(
        ItemGroupData,
        required=True,
        metadata=dict(
            description='The group to which the item belongs.'
        )
    )

    # * attribute: parent_item
    parent_item = ModelType(
        ItemData,
        required=True,
        metadata=dict(
            description='The parent item to which this subitem belongs.'
        )
    )

    # * attribute: column_values
    column_values = ListType(
        ModelType(ColumnValueData),
        default=[],
        metadata=dict(
            description='A list of column values associated with the item.'
        )
    )

    # * method: map
    def map(self) -> ItemDetailContract:
        """
        Maps the data object to an ItemDetail model.

        :return: An ItemDetail model instance.
        :rtype: ItemDetailContract
        """
        
        # Map the column values to their respective models.
        return super().map(
            ItemDetail,
            board_id=self.board.id,
            group_id=self.group.id,
            parent_item_id=self.parent_item.id if self.parent_item else None,
            column_values=[value.map() for value in self.column_values]
        )