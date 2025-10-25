"""Tiferet Monday Api Item Requests Proxy"""

# *** imports

# ** core
import json
from typing import (
    List,
    Dict,
    Any
)

# ** infra
from tiferet import DataObject

# ** app
from ...data import (
    ItemData,
    ItemDetailData,
    ColumnValueData    
)
from ...contracts import (
    ItemContract,
    ItemDetailContract,
    ColumnValueContract,
    ItemRepository
)
from .settings import MondayApiRequestsProxy

# *** proxies

# ** proxy: item_monday_api_proxy
class ItemMondayApiProxy(ItemRepository, MondayApiRequestsProxy):
    """
    Proxy for managing item-related operations using the Moncli client.
    """

    # * init
    def __init__(self, monday_api_key: str):
        """
        Initializes the ItemMondayProxy with the Monday.com API key.

        :param monday_api_key: API key for accessing the Monday.com API.
        :type monday_api_key: str
        """
        
        # Initialize the parent class with the API key.
        super().__init__(monday_api_key)

    # * method: query_detail_by_id
    def query_detail_by_id(self, item_id: str | int) -> ItemDetailContract:
        """
        Queries detailed information about an item by its ID using the Moncli client.
        :param item_id: ID of the item to retrieve details for.
        :type item_id: str | int
        :return: Detailed information about the item.
        :rtype: ItemDetailContract
        """

        # Execute the query to retrieve item details.
        data = self.execute_query(
            query="""
                query ($item_id: ID!) {
                    items(ids: [$item_id]) {
                        id
                        name
                        board {
                            id
                        }
                        group {
                            id
                        }
                        parent_item { 
                            id 
                        }
                        column_values {
                            id
                            column {
                                title
                                description
                            }
                            type
                            text
                        }
                    }
                }
            """,
            variables={'item_id': int(item_id)},
            start_node=lambda data: data.get('items', [])
        )

        # If no data is returned, return None.
        if not data:
            return None

        # Map the retrieved data to the ItemDetailContract.
        return DataObject.from_data(
            ItemDetailData,
            **data[0]
        ).map()

    # * method: query_by_ids
    def query_by_ids(self, item_ids: list[str | int]) -> list[ItemContract]:
        """
        Queries items by their IDs using the Moncli client.

        :param item_ids: List of item IDs to query.
        :type item_ids: list[str | int]
        :return: List of items matching the provided IDs.
        :rtype: list[ItemContract]
        """

        # Execute the query to retrieve items by their IDs.
        data = self.execute_query(
            query="""
                query ($item_ids: [ID!]) {
                    items(ids: $item_ids) {
                        id
                        name
                        board {
                            id
                        }
                        updates {
                            id
                            item_id
                            creator_id
                            body
                            replies {
                                id
                                body
                                creator_id
                            }
                        }
                    }
                }
            """,
            variables={'item_ids': [int(item_id) for item_id in item_ids]},
            start_node=lambda data: data.get('items', [])
        )

        # If no data is returned, return an empty list.
        if not data:
            return []

        # Map the retrieved items data to ItemContract.
        return [DataObject.from_data(
            ItemData,
            **item
        ).map() for item in data]
    
    # * method: query_column_values
    def query_column_values(self, item_id: str | int, column_ids: List[str] = []) -> List[ColumnValueContract]:
        """
        Queries column values for a given item ID using the Moncli client.

        :param item_id: ID of the item for which to query column values.
        :type item_id: str | int
        :return: List of column values for the specified item.
        :rtype: List[ColumnValueContract]
        """

        # Execute the query to retrieve column values.
        data = self.execute_query(
            query="""
                query ($item_id: ID!, $column_ids: [String!]) {
                    items (ids: [$item_id]) {
                        column_values (ids: $column_ids) {
                            id
                            column {
                                title
                                description
                                settings_str
                            }
                            type
                            value
                            ... on StatusValue {
                                index
                                text
                            }
                            ... on NumbersValue {
                                number
                            }
                            ... on BoardRelationValue {
                                linked_item_ids
                            }
                            ... on FileValue {
                                files {
                                    ... on FileDocValue {
                                        object_id
                                    }
                                    ... on FileLinkValue {
                                        file_id
                                    }
                                    ... on FileAssetValue {
                                        asset_id
                                    }
                                }
                            }
                            ... on PeopleValue {
                                persons_and_teams {
                                    id
                                    kind
                                }
                            }
                            ... on DocValue {
                                file {
                                    ... on FileDocValue {
                                        object_id
                                    }
                                }
                            }
                        }
                    }
                }
            """,
            variables={
                'item_id': int(item_id),
                'column_ids': column_ids
            },
            start_node=lambda data: data.get('items', [])[0].get('column_values', [])
        )

        # If no data is returned, return an empty list.
        if not data:
            return []

        # Map the retrieved column values data to ColumnValueContract.
        return tuple([DataObject.from_data(
            ColumnValueData,
            **cv
        ).map() for cv in data])
    
    # * method: query_subitems
    def query_subitems(self, parent_item_id: str | int) -> List[ItemContract]:
        """
        Queries subitems for a given parent item ID using the Moncli client.

        :param parent_item_id: ID of the parent item for which to query subitems.
        :type parent_item_id: str | int
        :return: List of subitems for the specified parent item.
        :rtype: List[ItemContract]
        """

        # Execute the query to retrieve subitems.
        data = self.execute_query(
            query="""
                query ($parent_item_id: [ID!]!) {
                    items (ids: $parent_item_id) {
                        subitems {
                            id
                            name
                            board {
                                id
                            }
                            updates {
                                id
                                item_id
                                creator_id
                                body
                                replies {
                                    id
                                    body
                                    creator_id
                                }
                            }
                        }
                    }
                }
            """,
            variables={'parent_item_id': int(parent_item_id)},
            start_node=lambda data: data.get('items', [])[0].get('subitems', [])
        )

        # If no data is returned, return an empty list.
        if not data:
            return []

        # Map the retrieved subitems data to SubitemContract.
        return [DataObject.from_data(
            ItemData,
            **subitem
        ).map() for subitem in data]

    # * method: update_simple_column_value
    def update_simple_column_value(self, item_id: str | int, board_id: str | int, column_id: str, value: str):
        """
        Updates the value of a simple column for the specified item using the Moncli client.

        :param item_id: ID of the item to be updated.
        :type item_id: str | int
        :param board_id: ID of the board to which the item belongs.
        :type board_id: str | int
        :param column_id: ID of the column to be updated.
        :type column_id: str
        :param value: New value for the column.
        :type value: str
        """

        # Execute the mutation to update the simple column value.
        data = self.execute_query(
            query="""
                mutation ($item_id: ID!, $board_id: ID!, $column_id: String!, $value: String!) {
                    change_simple_column_value(item_id: $item_id, board_id: $board_id, column_id: $column_id, value: $value) {
                        id
                        name
                        board {
                            id
                        }
                    }
                }
            """,
            variables={
                'item_id': int(item_id),
                'board_id': int(board_id),
                'column_id': column_id,
                'value': value
            },
            start_node=lambda data: data.get('change_simple_column_value', None)
        )

        # Map the result to ItemData and return.
        return DataObject.from_data(
            ItemData,
            **data
        ).map() if data else None
    
    # * method: create_subitem
    def create_subitem(self, parent_item_id: str | int, item_name: str, column_values: Dict[str, Any] = {}) -> ItemContract:
        """
        Creates a subitem under the specified item using the Moncli client.

        :param parent_item_id: ID of the parent item under which the subitem will be created.
        :type parent_item_id: str | int
        :param item_name: Name of the subitem to be created.
        :type item_name: str
        :return: Result of the subitem creation operation.
        :rtype: Any
        """

        # Execute the mutation to create a subitem.
        data = self.execute_query(
            query="""
                mutation ($parent_item_id: ID!, $item_name: String!, $column_values: JSON!) {
                    create_subitem(parent_item_id: $parent_item_id, item_name: $item_name, column_values: $column_values) {
                        id
                        name
                        board {
                            id
                        }
                    }
                }
            """,
            variables={
                'parent_item_id': int(parent_item_id),
                'item_name': item_name,
                'column_values': json.dumps(column_values)
            },
            start_node=lambda data: data.get('create_subitem', None)
        )

        return DataObject.from_data(
            ItemData,
            **data
        ).map() if data else None