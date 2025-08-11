from src.oni_ai_agents.services.oni_save_parser.compressed_blocks import CompressedBlocksScanner
from src.oni_ai_agents.services.oni_save_parser.duplicant_decoder import DuplicantDecoder
from src.oni_ai_agents.services.oni_save_parser.header_reader import SaveHeaderReader
from src.oni_ai_agents.services.oni_save_parser.ksav_index import KSAVGroupCounter
from src.oni_ai_agents.services.oni_save_parser.metadata_builder import MetadataBuilder


def test_modularization_classes_instantiation():
    # Smoke test: ensure modules import and classes can be instantiated
    _ = CompressedBlocksScanner()
    _ = SaveHeaderReader()
    _ = KSAVGroupCounter()
    _ = DuplicantDecoder()
    _ = MetadataBuilder()


