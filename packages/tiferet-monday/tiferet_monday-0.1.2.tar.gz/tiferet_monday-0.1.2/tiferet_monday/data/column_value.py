"""Tiferet Monday Column Value Data Objects"""

# *** imports

# ** infra
from tiferet import (
    DataObject,
    StringType,
    IntegerType,
    ListType,
    ModelType,
    DictType,
)

# ** app
from ..models import (
    ColumnValue
)
from ..contracts import (
    ColumnValueContract
)

# *** data

# ** data: column_data
class ColumnData(DataObject):
    """
    Represents a column in a Monday.com item.
    """

    class Options():
        """
        Options for the ColumnData class.
        """
        serialize_when_none = False
        roles = dict(
            to_model=DataObject.deny('title', 'description', 'settings_str'),
            to_data=DataObject.allow()
        )

    # * attribute: title
    title = StringType(
        metadata=dict(
            description='The title of the column.'
        )   
    )

    # * attribute: description
    description = StringType(
        metadata=dict(
            description='A description of the column.'
        )
    )

    # * attribute: settings_str
    settings_str = StringType(
        metadata=dict(
            description='A JSON string representing the settings of the column.'
        )
    )

# ** data: column_value_data
class ColumnValueData(DataObject, ColumnValue):
    """
    Represents a column value in a Monday.com item.
    """

    class Options():
        """
        Options for the ColumnValueData class.
        """
        serialize_when_none = False
        roles = {
            'to_data': DataObject.allow(),
            'to_model': DataObject.deny('column', 'linked_item_ids', 'files')
        }

    # * attribute: column
    column = ModelType(
        ColumnData,
        required=True,
        metadata=dict(
            description='The column to which the value belongs.'
        )
    )
    
    # * attribute: index
    index = IntegerType(
        metadata=dict(
            description='The index of the status in the column (for Status columns).'
        )
    )

    # * attribute: text
    text = StringType(
        metadata=dict(
            description='The text representation of the column value (for Status columns).'
        )
    )

    # * attribute: persons_and_teams
    persons_and_teams = ListType(
        DictType(StringType),
        default=[],
        metadata=dict(
            description='A list of persons and teams associated with this column value (for People columns).'
        )
    )

    # * attribute: number
    number = IntegerType(
        metadata=dict(
            description='The numeric representation of the column value (for Number columns).'
        )
    )

    # * attribute: linked_item_ids
    linked_item_ids = ListType(
        IntegerType,
        default=[],
        metadata=dict(
            description='A list of IDs of items linked to this column value (for Board Relation columns).'
        )
    )

    # * attribute: files
    files = ListType(
        DictType(StringType),
        default=[],
        metadata=dict(
            description='A list of files associated with this column value (for File columns).'
        )
    )

    # * attribute: file
    file = DictType(
        StringType, 
        metadata=dict(
            description='A single file associated with this column value (for File columns).'
        )
    )

    # * method: map
    def map(self, map_to_type: bool = True) -> ColumnValueContract:
        """
        Maps the data object to a ColumnValue model.

        :param map_to_type: Whether to map to a specific ColumnValue subtype based on the column type.
        :type map_to_type: bool
        :return: A ColumnValue model instance.
        :rtype: ColumnValueContract
        """
        
        # Set the default attributes for the ColumnValue model.
        attributes = dict(
            name=self.column.title,
            description=self.column.description,
            settings_str=self.column.settings_str,
        )

        # If map_to_type is False, return a generic ColumnValue model.
        if not map_to_type:
            return super().map(
                ColumnValue,
                **attributes
            )

        # If the column type is 'status', set the value to a JSON string of index and text.
        if self.type == 'status':
            attributes.update(dict(
                index=self.index,
                text=self.text            
            ))

        if self.type == 'people':
            attributes.update(dict(
                persons_and_teams=self.persons_and_teams            
            ))

        # If the column type is 'number', set the value to the numeric representation.
        if self.type == 'number':
            attributes.update(dict(
                number=self.number            
            ))
        
        # If the column type is 'board_relation', set the value to a JSON string of linked item IDs.
        if self.type == 'board_relation':
            attributes.update(dict(
                linked_item_ids=self.linked_item_ids            
            ))
        
        # If the column type is 'file', set the value to a list of file ids.
        if self.type == 'file':
            attributes.update(dict(
                files=self.files            
            ))
        
        # If the column type is 'doc', set the value to the file dictionary.
        if self.type == 'doc':
            attributes.update(dict(
                file=self.file            
            ))

        # Map to the appropriate ColumnValue subtype based on the column type.
        return super().map(
            ColumnValue,
            **attributes
        )