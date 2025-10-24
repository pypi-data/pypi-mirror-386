from typing import Any, Callable, Generic, List, Dict, Text, Optional, Tuple, Union, TypeVar, Type, cast
from neo4j import AsyncManagedTransaction, AsyncResult, AsyncSession
from ewoxcore.client.paging_args import PagingArgs
from ewoxcore.utils.json_util import JsonUtil
from ewoxcore.utils.dictionary_util import DictionaryUtil
from ewoxcore.utils.boolean_util import BooleanUtil
from ewoxcore.client.paging_model import PagingModel

T = TypeVar('T')

class RepositoryBase:
    """
    Base class for repositories.    
    This class provides a base class for all repositories.
    """
    def __init__(self, cypher_path:str) -> None:
        """
        Initialize the repository with the path to the Cypher queries.
        :param cypher_path: Path to the directory containing Cypher query files.
        """
        if not cypher_path:
            raise ValueError("Cypher path cannot be empty.")

        self._cypher_path:str = cypher_path


    def get_query(self, file_name: str) -> str:
        """
        Load a Cypher query from a file.
        :param path: Path to the directory containing repository file.
        :param file_name: Name to the Cypher query file.
        :return: The Cypher query as a string.
        """
        with open(self._cypher_path + "/queries/" + file_name, "r") as file:
            return file.read()


    def get_mutation(self, file_name: str) -> str:
        """
        Load a Cypher query from a file.
        :param file_name: Name to the Cypher query file.
        :return: The Cypher query as a string.
        """
        with open(self._cypher_path + "/mutations/" + file_name, "r") as file:
            return file.read()


    async def get_items(self,
        session:AsyncSession,
        query:str,
        params: dict[str, Any],
        model_class: Optional[Type[T]] = None,
        result_name:str = "result"
    ) -> list[T]:
        """ Retrieve items from the database using a Cypher query.
        :param session: The database session to use.
        :param query: The Cypher query to execute. 
        :param params: The parameters to pass to the query.
        :param model_class: The class to use for mapping the results.
        :param result_name: The name of the result field in the query.
        :return: A list of items mapped to the specified model class.
        """
        records = await session.execute_read(self._get_items, params, query=query, result_name=result_name)
        if (records is None or len(records) == 0):
            return []

        if (model_class is None):
            return records

        return [model_class(record) for record in records]


    async def _get_items(self, tx:AsyncManagedTransaction, params:Dict[str, Any], query:str, result_name:str) -> list[dict[str, Any]]:
        result: AsyncResult = await tx.run(query=query, parameters=params)
        records = await result.data()
        if not records:
            return []

        items:list[dict[str, Any]] = []
        for record in records:
            item:dict[str, Any] = record[result_name]
            items.append(item)

        return items


    async def get_item(self,
        session:AsyncSession,
        query:str,
        params: dict[str, Any],
        model_class: Type[T],
        result_name:str = "result"
    ) -> Optional[T]:
        """ Retrieve items from the database using a Cypher query.
        :param session: The database session to use.
        :param query: The Cypher query to execute. 
        :param params: The parameters to pass to the query.
        :param model_class: The class to use for mapping the results.
        :param result_name: The name of the result field in the query.
        :return: An item mapped to the specified model class.
        """
        records = await session.execute_read(self._get_item, params, query=query, result_name=result_name)
        if not records:
            return None
       
        item:T = model_class(records[0])

        return item


    async def get_paging_item(self,
        session:AsyncSession,
        query:str,
        args:PagingArgs,
        params: dict[str, Any],
        model_class: type[T],
        factory:Callable[[Any], T] = None,
        result_name:str = "result"
    ) -> Optional[PagingModel[T]]:
        """ Retrieve items from the database using a Cypher query.
        :param session: The database session to use.
        :param query: The Cypher query to execute. 
        :param params: The parameters to pass to the query.
        :param model_class: The class to use for mapping the results.
        :param result_name: The name of the result field in the query.
        :return: A paging model mapped to the specified model class.
        """
        args_params:dict[str, Any] = args.to_dict()
        args_params.update(params)

        records = await session.execute_read(self._get_item, args_params, query=query, result_name=result_name)
        if not records:
            return None

        factory = factory if (factory is not None) else model_class
        item:PagingModel[T] = PagingModel[T](records[0], item_factory=factory)
        item.skip = args.skip + args.num
        item.num = args.num

        return item


    async def _get_item(self, tx:AsyncManagedTransaction, params:Dict[str, Any], query:str, result_name:str) -> Any:
        result: AsyncResult = await tx.run(query=query, parameters=params)
        record = await result.single()

        return record


    async def save_item(self, 
        session:AsyncSession, 
        mutation:str,
        model: T
        ) -> bool:
        """ Save an item to the database using a Cypher mutation."""
        try:
            entity:dict[str, Any] = DictionaryUtil.to_dict(model)
            result:bool = await session.execute_write(self._save_item, entity, mutation=mutation)
            return result
        except Exception as e:
            print(f"Error: {e}")
            raise
        

    async def save_entity(self, 
        session:AsyncSession, 
        mutation:str,
        entity:dict[str, Any]
        ) -> bool:
        """ Save an entity to the database using a Cypher mutation."""
        try:
            result:bool = await session.execute_write(self._save_item, entity, mutation=mutation)
            return result
        except Exception as e:
            print(f"Error: {e}")
            raise


    async def _save_item(self, tx:AsyncManagedTransaction, params:Dict[str, Any], mutation:str) -> bool:
        result: AsyncResult = await tx.run(query=mutation, parameters=params)
        record = await result.single()
        if not record:
            return False
 
        return True


    async def exists_item(self,
        session:AsyncSession,
        query:str,
        params: dict[str, Any],
        result_name:str = "result"
    ) -> bool:
        records = await session.execute_read(self._get_item, params, query=query, result_name=result_name)
        if not records:
            return None
        
        result:bool = BooleanUtil.get_safe_bool(records[0])       

        return result


    async def execute_write_entity(self, 
        session:AsyncSession, 
        mutation:str,
        entity:dict[str, Any]
        ) -> bool:
        """ Execute a write mutation with the given entity."""
        try:
            result:bool = await session.execute_write(self._save_item, entity, mutation=mutation)
            return result
        except Exception as e:
            print(f"Error: {e}")
            raise
