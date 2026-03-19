from .BaseDataModel import BaseDataModel
from .mongodb_schemas import Project
from .enums.DatabaseEnums import DatabaseEnum

class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DatabaseEnum.COLLECTION_PROJECT_NAME.value]
    
    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client) # creates an instance of the ProjectModel class, passing the db_client to the constructor
        await instance.init_collection()
        return instance
    
    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DatabaseEnum.COLLECTION_PROJECT_NAME.value not in all_collections:
            self.db_client[DatabaseEnum.COLLECTION_PROJECT_NAME.value]
            indexes = Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index.get("unique", False)
                )
    
    async def create_project(self, project: Project):
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))  # insert_one takes a dict, we need to convert the Project object to a dict  
        project.id = result.inserted_id
        return project
    
    async def get_or_create_project(self, project_id: str):

        record = await self.collection.find_one({
            "project_id": project_id
        })
        if record is None:
            project = Project(project_id=project_id)
            project = await self.create_project(project)
            return project
        
        return Project(**record) # find_one returns a dict, we need to convert it to a Project object
    
    # pagination for projects: dividing large datasets or content into smaller, manageable pages to improve performance, and reduce server load.
    async def get_all_projects(self, page: int = 1, page_size: int = 10):

        #count total number of documents in the collection
        total_projects = await self.collection.count_documents({})

        # calculate the number of pages
        total_pages = total_projects // page_size
        if total_projects % page_size > 0:
            total_pages += 1
        
        cursor = self.collection.find().skip((page - 1) * page_size)
        projects = []
        async for document in cursor:
            projects.append(Project(**document))

        return projects, total_pages                        





    

    

