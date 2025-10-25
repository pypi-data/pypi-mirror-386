"""Tiferet Monday Column Value Models"""

# *** imports

# ** core
from typing import List

# ** app
from tiferet import (
    ModelObject,
    StringType,
    IntegerType,
    ListType,
    DictType,
)

# ** model: column_value
class ColumnValue(ModelObject):
    """
    Represents a column value in a Monday.com item.
    """

    # * attribute: id
    id = StringType(
        required=True,
        metadata=dict(
            description='The unique identifier of the column.'
        )
    )

    # * attribute: name
    name = StringType(
        required=True,
        metadata=dict(
            description='The column title.'
        )
    )

    # * attribute: type
    type = StringType(
        required=True,
        metadata=dict(
            description='The type of the column value.'
        )
    )

    # * attribute: text
    text = StringType(
        metadata=dict(
            description='The text representation of the column value.'
        )
    )

    # * attribute: value
    value = StringType(
        metadata=dict(
            description='The actual value of the column.'
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

    # * method: new
    @staticmethod
    def new(
        id: str,
        name: str,
        type: str,
        text: str = None,
        value: str = None,
        description: str = None,
        settings_str: str = None,
        **kwargs
    ) -> 'ColumnValue':
        """
        Creates a new instance of ColumnValue.

        :param id: The unique identifier of the column.
        :type id: str
        :param name: The column title.
        :type name: str
        :param type: The type of the column value.
        :type type: str
        :param text: The text representation of the column value.
        :type text: str, optional
        :param value: The actual value of the column.
        :type value: str, optional
        :param description: A description of the column.
        :type description: str, optional
        :param settings_str: A JSON string representing the settings of the column.
        :type settings_str: str, optional
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A new instance of ColumnValue.
        :rtype: ColumnValue
        """
        
        # Create a mapping of column types to their corresponding classes.
        type_map = {
            'status': StatusValue,
            'people': PeopleValue,
            'numbers': NumbersValue,
            'board_relation': BoardRelationValue,
            'file': FileValue,
            'doc': DocValue
        }

        # Return a new instance of the appropriate class.
        return ModelObject.new(
            type_map.get(type, ColumnValue),
            id=id,
            name=name,
            type=type,
            text=text,
            value=value,
            description=description,
            settings_str=settings_str,
            **kwargs
        )

# ** model: status_value
class StatusValue(ColumnValue):
    """
    Represents a status column value in a Monday.com item.
    """

    # * attribute: index
    index = IntegerType(
        metadata=dict(
            description='The index of the status (for Status columns).'
        )
    )

    # * attribute: text
    text = StringType(
        metadata=dict(
            description='The text representation of the status (for Status columns).'
        )
    )

# ** model: people_value
class PeopleValue(ColumnValue):
    """
    Represents a people column value in a Monday.com item.
    """

    # * attribute: persons_and_teams
    persons_and_teams = ListType(
        DictType(StringType),
        default=[],
        metadata=dict(
            description='A list of persons and teams associated with this column value (for People columns).'
        )
    )

    # * method: get_person_ids
    def get_person_ids(self) -> List[str]:
        """
        Extracts and returns a list of person IDs from the persons_and_teams.

        :return: A list of person IDs.
        :rtype: list[str]
        """

        # Extract person IDs from the persons_and_teams list of dictionaries.
        person_ids = []
        for entry in self.persons_and_teams:
            if entry.get('kind') == 'person':
                person_ids.append(entry['id'])
        return person_ids

# ** model: numbers_value
class NumbersValue(ColumnValue):
    """
    Represents a number column value in a Monday.com item.
    """

    # * attribute: number
    number = IntegerType(
        metadata=dict(
            description='The numeric representation of the column value.'
        )
    )

# ** model: board_relation_value
class BoardRelationValue(ColumnValue):
    """
    Represents a board relation column value in a Monday.com item.
    """

    # * attribute: linked_item_ids
    linked_item_ids = ListType(
        IntegerType,
        default=[],
        metadata=dict(
            description='A list of item IDs linked in the board relation column.'
        )
    )

# ** model: file_value
class FileValue(ColumnValue):
    """
    Represents a file column value in a Monday.com item.
    """

    # * attribute: files
    files = ListType(
        DictType(StringType),
        default=[],
        metadata=dict(
            description='A list of files associated with the file column.'
        )
    )

    # * method: get_object_ids
    def get_object_ids(self) -> List[str]:
        """
        Extracts and returns a list of object IDs from the files.

        :return: A list of object IDs.
        :rtype: list[str]
        """

        # Get list of object ids from the files list of dictionaries.
        object_ids = []
        for file in self.files:
            if 'object_id' in file:
                object_ids.append(file['object_id'])
        return object_ids
    
# ** model: doc_value
class DocValue(ColumnValue):
    """
    Represents a document column value in a Monday.com item.
    """

    # * attribute: file
    file = DictType(
        StringType, 
        metadata=dict(
            description='A single file associated with this column value (for File columns).'
        )
    )

    # * method: get_object_id
    def get_object_id(self) -> str:
        """
        Extracts and returns the object ID from the file.

        :return: The object ID.
        :rtype: str
        """

        # Get object id from the file dictionary.
        return self.file.get('object_id', None)