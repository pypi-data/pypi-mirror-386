# *** imports

# ** core
from typing import List

# ** infra
from tiferet import DataObject

# ** app
from ...models import Document, DocumentBlock
from ...data import DocumentData
from .settings import MondayApiRequestsProxy

# *** proxies

# ** proxy: document_monday_proxy
class DocumentMondayApiProxy(MondayApiRequestsProxy):
    """
    Proxy for managing document-related operations using the Monday.com API.
    """

    # * init
    def __init__(self, monday_api_key: str):
        """
        Initializes the DocumentMondayProxy with the Monday.com API key.

        :param monday_api_key: API key for accessing the Monday.com API.
        :type monday_api_key: str
        """
        
        # Initialize the parent class with the API key.
        super().__init__(monday_api_key)

    # * method: create_doc_in_column
    def create_doc_in_column(self, item_id: str | int, column_id: str) -> Document:
        """
        Creates a document in the specified column of an item using the Monday.com API.

        :param item_id: ID of the item where the document will be created.
        :type item_id: str | int
        :param column_id: ID of the column where the document will be created.
        :type column_id: str
        :return: The created document.
        :rtype: Document
        """
        
        # Execute the mutation to create a document in the specified column.
        data = self.execute_query(
            query=f"""
                mutation {{
                    create_doc(location: {{board: {{item_id: {int(item_id)}, column_id: "{column_id}"}}}}) {{
                        id
                        name
                        object_id
                    }}
                }}
            """,
            start_node=lambda data: data.get('create_doc', {})
        )

        # Return the created document as a DocumentContract instance.
        return DataObject.from_data(
            DocumentData,
            **data
        ).map()
    
    # * method: query_by_object_ids
    def query_by_object_ids(self, object_ids: List[str]) -> List[Document]:
        """
        Queries documents by their object IDs using the Monday.com API.

        :param object_ids: List of object IDs of the documents to retrieve.
        :type object_ids: List[str]
        :return: List of documents matching the specified object IDs.
        :rtype: List[Document]
        """

        # Execute the query to retrieve documents by their object IDs.
        data = self.execute_query(
            query="""
                query ($objectIds: [ID!]!) {
                    docs (object_ids: $objectIds) {
                        id
                        name
                        object_id
                        blocks {
                            id
                            type
                            content
                        }
                    }
                }
            """,
            variables={'objectIds': [int(object_id) for object_id in object_ids]},
            start_node=lambda data: data.get('docs', [])
        )

        # Map the retrieved document data to DocumentContract instances.
        return [DataObject.from_data(DocumentData, **doc).map() for doc in data]
    
    # * method: update_doc_name
    def update_doc_name(self, doc_id: str | int, name: str):
        """
        Updates the name of a specified monday.com document.

        :param doc_id: ID of the document to rename.
        :type doc_id: str | int
        :param name: New name for the document.
        :type name: str
        """
        
        # Execute the mutation to update the document's name.
        self.execute_query(
            query="""
                mutation ($docId: ID!, $name: String!) {
                    update_doc_name(docId: $docId, name: $name) 
                }
            """,
            variables={
                'docId': int(doc_id),
                'name': name
            },
            api_version='2025-10'
        )

    # * method: query_doc_blocks
    def query_doc_blocks(self, doc_id: str | int, limit: int = 25, page: int = 1) -> List[DocumentBlock]:
        """
        Reads the blocks of a specified document using the Monday.com API.

        :param doc_id: ID of the document to read blocks from.
        :type doc_id: str | int
        :param limit: Maximum number of blocks to read (default is 25).
        :type limit: int
        :param page: Page number for pagination (default is 1).
        :type page: int
        :return: List of blocks in the document.
        :rtype: List[DocumentBlock]
        """
        
        # Execute the query to retrieve the document's blocks.
        data = self.execute_query(
            query="""
                query ($docId: [ID!]!, $limit: Int, $page: Int) {
                    docs (ids: $docId) {
                        blocks (limit: $limit, page: $page) {
                            id
                            type
                            content
                        }
                    }
                }
            """,
            variables=dict(
                docId=int(doc_id), 
                limit=limit,
                page=page
            ),
            start_node=lambda data: data.get('docs')
        )

        # If no data is returned, return an empty list.
        if not data[0]:
            return []

        # Map the retrieved document data to extract blocks.
        return DataObject.from_data(DocumentData, **data[0]).blocks
    
    # * method: create_doc_block
    def create_doc_block(self, doc_id: str | int, type: str, content: str, after_block_id: str = None) -> str:
        """
        Creates a new block in the specified document using the Monday.com API.

        :param doc_id: ID of the document where the block will be created.
        :type doc_id: str | int
        :param type: Type of the block to be created.
        :type type: str
        :param content: Content of the block.
        :type content: str
        :param after_block_id: ID of the block after which the new block will be inserted (optional).
        :type after_block_id: str
        :return: The id of the created document block.
        :rtype: str
        """
        
        # Execute the mutation to create a new document block.
        data = self.execute_query(
            query="""
                mutation ($docId: ID!, $type: DocBlockContentType!, $content: JSON!, $afterBlockId: String) {
                    create_doc_block(doc_id: $docId, type: $type, content: $content, after_block_id: $afterBlockId) {
                        id
                    }
                }
            """,
            variables={
                'docId': int(doc_id),
                'type': type,
                'content': content,
                'afterBlockId': after_block_id
            },
            start_node=lambda data: data.get('create_doc_block', {})
        )

        # If no data is returned, return None.
        if not data:
            return None

        # Return the ID of the created document block.
        return data.get('id', None)