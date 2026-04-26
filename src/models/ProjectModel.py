from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from .enums.DatabaseEnums import DatabaseEnum
from sqlalchemy.future import select
from sqlalchemy import func


class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.db_client = db_client
    
    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client) # creates an instance of the ProjectModel class, passing the db_client to the constructor
        return instance
    
    
    async def create_project(self, project: Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        return project
    
    async def get_or_create_project(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                project = await session.execute(query)
                project = project.scalar_one_or_none()
                if project is None:
                    project_record = Project(
                        project_id=project_id
                    )
                    project = await  self.create_project(project_record)
                    return project
                else:
                    return project
                

    # pagination for projects: dividing large datasets or content into smaller, manageable pages to improve performance, and reduce server load.
    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        async with self.db_client() as session:
            async with session.begin():
                total_documents = await session.execute(select(
                    func.count(Project.project_id) # primary key of the Project table, counting the total number of projects in the database
                ))
                total_documents = total_documents.scalar_one()
                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1
                
                query = select(Project).offset((page - 1) * page_size).limit(page_size)
                projects =await session.execute(query).scalars().all()
                return projects, total_pages





    

    

