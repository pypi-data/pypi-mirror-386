import os
from pathlib import Path

from bioguider.agents.evaluation_tutorial_task import EvaluationTutorialTask
from bioguider.agents.evaluation_userguide_task import EvaluationUserGuideTask
from bioguider.database.code_structure_db import CodeStructureDb
from bioguider.utils.constants import ProjectMetadata

from ..agents.identification_task import IdentificationTask
from ..rag.rag import RAG
from ..utils.file_utils import parse_repo_url
from ..utils.code_structure_builder import CodeStructureBuilder
from ..database.summarized_file_db import SummarizedFilesDb
from ..agents.evaluation_readme_task import EvaluationREADMETask
from ..agents.evaluation_installation_task import EvaluationInstallationTask
from ..agents.evaluation_submission_requirements_task import EvaluationSubmissionRequirementsTask
from ..agents.collection_task import CollectionTask

class EvaluationManager:
    def __init__(self, llm, step_callback):
        self.rag = None
        self.llm = llm
        self.step_callback = step_callback
        self.repo_url: str | None = None
        self.project_metadata: ProjectMetadata | None = None

    def prepare_repo(self, repo_url: str):
        self.repo_url = repo_url
        self.rag = RAG()
        self.rag.initialize_db_manager()
        self.rag.initialize_repo(repo_url_or_path=repo_url)
        
        author, repo_name = parse_repo_url(repo_url)
        self.summary_file_db = SummarizedFilesDb(author, repo_name)
        self.code_structure_db = CodeStructureDb(author, repo_name)
        code_structure_builder = CodeStructureBuilder(
            repo_path=self.rag.repo_dir, 
            gitignore_path=Path(self.rag.repo_dir, ".gitignore"), 
            code_structure_db=self.code_structure_db
        )
        code_structure_builder.build_code_structure()

    def identify_project(self) -> ProjectMetadata:
        repo_path = self.rag.repo_dir
        gitignore_path = Path(repo_path, ".gitignore")

        identfication_task = IdentificationTask(
            llm=self.llm,
            step_callback=self.step_callback,
        )
        identfication_task.compile(
            repo_path=repo_path,
            gitignore_path=gitignore_path,
            db=self.summary_file_db,
        )
        language = identfication_task.identify_primary_language()
        project_type = identfication_task.identify_project_type()
        meta_data = identfication_task.identify_meta_data()

        self.project_metadata = ProjectMetadata(
            url=self.repo_url,
            project_type=project_type,
            primary_language=language,
            repo_name=meta_data["name"] if "name" in meta_data else "",
            description=meta_data["description"] if "description" in meta_data else "",
            owner=meta_data["owner"] if "owner" in meta_data else "",
            license=meta_data["license"] if "license" in meta_data else "",
        )
        return self.project_metadata
    
    def evaluate_readme(self) -> tuple[any, list[str]]:
        task = EvaluationREADMETask(
            llm=self.llm,
            repo_path=self.rag.repo_dir,
            gitignore_path=Path(self.rag.repo_dir, ".gitignore"),
            meta_data=self.project_metadata,
            step_callback=self.step_callback,
            summarized_files_db=self.summary_file_db,
        )
        # readme_files = self._find_readme_files()
        results, readme_files = task.evaluate()
        return results, readme_files
    
    def evaluate_installation(self):
        evaluation_task = EvaluationInstallationTask(
            llm=self.llm,
            repo_path=self.rag.repo_dir,
            gitignore_path=Path(self.rag.repo_dir, ".gitignore"),
            meta_data=self.project_metadata,
            step_callback=self.step_callback,
        )
        evaluation, files = evaluation_task.evaluate()
        return evaluation, files
    
    def evaluate_submission_requirements(
        self,
        readme_files_evaluation: dict | None = None,
        installation_files: list[str] | None = None,
        installation_evaluation: dict[str] | None = None,
    ):
        evaluation_task = EvaluationSubmissionRequirementsTask(
            llm=self.llm,
            repo_path=self.rag.repo_dir,
            gitignore_path=Path(self.rag.repo_dir, ".gitignore"),
            meta_data=self.project_metadata,
            step_callback=self.step_callback,
            summarized_files_db=self.summary_file_db,
            readme_files_evaluation=readme_files_evaluation,
            installation_files=installation_files,
            installation_evaluation=installation_evaluation,
        )
        evaluation, files = evaluation_task.evaluate()

        return evaluation, files

    def evaluate_userguide(self):
        evaluation_task = EvaluationUserGuideTask(
            llm=self.llm,
            repo_path=self.rag.repo_dir,
            gitignore_path=Path(self.rag.repo_dir, ".gitignore"),
            meta_data=self.project_metadata,
            step_callback=self.step_callback,
            summarized_files_db=self.summary_file_db,
            code_structure_db=self.code_structure_db,
        )
        evaluation, files = evaluation_task.evaluate()
        return evaluation, files
    
    def evaluate_tutorial(self):
        evaluation_task = EvaluationTutorialTask(
            llm=self.llm,
            repo_path=self.rag.repo_dir,
            gitignore_path=Path(self.rag.repo_dir, ".gitignore"),
            meta_data=self.project_metadata,
            step_callback=self.step_callback,
            summarized_files_db=self.summary_file_db,
            code_structure_db=self.code_structure_db,
        )
        evaluation, files = evaluation_task.evaluate()
        return evaluation, files

        
        
    

