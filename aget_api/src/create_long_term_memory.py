from dotenv import load_dotenv
load_dotenv()

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

#from config.setings import settings
from data_models.models import TopicsExtract
from knowledge_base.knowledge_base_creation import KnowledgeBaseCreator

from pathlib import Path
import click

@click.command()
@click.option(
    "--metadata_file",
    type=click.Path(exists=True, path_type=Path),
    default=r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\data.json", #settings.DATA_FILE_PATH,
    help="Path to the data extraction JSON file."
)
def main(metadata_file : Path):
    """CLI command to create long-term memory for AgeT.

    Args:
        metadata_file: Path to the topic extraction metadata JSON file.
    """

    topics = TopicsExtract.load_from_json(datafile_path=metadata_file)
    print(f"Topics Running : {topics}")
    
    ltm_obj = KnowledgeBaseCreator()
    ltm_obj.create_knowledge(topics)
    

    return


if __name__ == "__main__":
    main()





