# document_ocr.py
# Standard library imports
import os
import tempfile
import logging

# Local imports
from ..converter.document_ocr_to_text import get_document_ocr
from ..loader.downloader.downloader import Downloader
from ..converter.pdf import convert_to_pdf

logger = logging.getLogger(__name__)


class DocumentOCRLoader:

    def __init__(self,
                 source: str,
                 s3_client: object = None,
                 document_aws_bucket: str = None,
                 gcs_client: object = None,
                 document_gcs_bucket: str = None,
                 llm_api_key: str = None,
                 temp_dir: str = 'temp',
                 markdown_output: bool = True,
                 target_size: int = 1,
                 page_range: tuple[int, int] = None,
                 timeout_minutes: int = None,
                 **kwargs
                 ):
        """
        Initialize the DocumentOCRLoader with cloud storage and LLM configurations.

        Handles document loading and storage operations across AWS S3 and Google Cloud Storage.
        Sets up temporary directory for processing files.

        Args:
            source (str): Source of the document. Must be either "cloud" or "local".
            markdown_output (bool, optional): If True, the extracted text will be formatted as Markdown.
                Defaults to True.
            s3_client (boto3.client, optional): AWS S3 client for S3 operations. Defaults to None.
            document_aws_bucket (str, optional): S3 bucket name for document storage. Defaults to None.
            gcs_client (google.cloud.storage.Client, optional): GCS client for Cloud Storage operations.
                Defaults to None.
            document_gcs_bucket (str, optional): GCS bucket name for document storage. Defaults to None.
            llm_api_key (str, optional): API key for language model service. Defaults to None.
            temp_dir (str, optional): Path for temporary file storage. Defaults to "temp".
            target_size (int, optional): Target file size in bytes. Defaults to 1MB
            page_range (tuple): Optional page range to extract (start, end)
            timeout_minutes (int, optional): Timeout in minutes. Defaults to None.

        Raises:
            ValueError: If cloud storage clients are provided without bucket names
            OSError: If temp directory creation fails
        """
        self.source = source
        self.markdown_output = markdown_output
        self.s3_client = s3_client
        self.document_aws_bucket = document_aws_bucket
        self.gcs_client = gcs_client
        self.document_gcs_bucket = document_gcs_bucket
        self.llm_api_key = llm_api_key
        self.target_size = target_size
        self.page_range = page_range
        self.type = "document_ocr"
        self.timeout_minutes = timeout_minutes

        # Set up custom temp directory
        self.temp_dir = os.path.abspath(temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        tempfile.tempdir = self.temp_dir

    def download_document(self, file_path, temp_file_path):
        """
        Download a document from S3 or GCS to a local temporary path.

        Args:
            file_path (str): Path to file in S3 or GCS bucket
            temp_file_path (str): Local path to save the downloaded file

        Returns:
            str: Path to the downloaded file

        Raises:
            ClientError: If download operation fails
        """
        if self.s3_client is not None:
            downloader = Downloader(s3_client=self.s3_client, document_aws_bucket=self.document_aws_bucket)
            downloader.download_file_from_s3(file_path, temp_file_path)
            logger.info(f'Downloaded {file_path} to {temp_file_path}')
            return temp_file_path
        elif self.gcs_client is not None:
            downloader = Downloader(gcs_client=self.gcs_client, document_gcs_bucket=self.document_gcs_bucket)
            downloader.download_file_from_gcs(file_path, temp_file_path)
            logger.info(f'Downloaded {file_path} to {temp_file_path}')
            return temp_file_path

    def convert_doc_to_pdf(self, file_prefix: str, input_file: str) -> str:
        """
        Convert any document format to PDF using cloud storage and LibreOffice.

        Downloads the document from S3 or GCS using file_prefix to locate it,
        saves it locally to input_file path, and converts to PDF using LibreOffice.
        Handles cleanup of temporary files.

        Args:
            file_prefix (str): Full cloud storage path (s3:// or gcs:// URI)
            input_file (str): Temporary local path to save downloaded file

        Returns:
            str: Path to the generated PDF file in temporary directory

        Raises:
            FileNotFoundError: If no matching document found in cloud storage
            ConversionError: If LibreOffice conversion fails
            AttributeError: If neither S3 nor GCS client is configured
            ClientError: If cloud storage operations fail
        """
        logger.info(f"file_prefix: {file_prefix}")
        logger.info(f"input_file: {input_file}")

        # Create a temporary file for output
        fd, output_file = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)  # Close file descriptor explicitly

        logger.info("Using LibreOffice")
        convert_to_pdf(input_file=input_file, output_file=output_file, original_file=file_prefix)
        logger.info("Document converted to pdf")
        os.remove(input_file)
        return output_file

    def get_text_from_document_ocr(self, file_path):
        """
        Extract text from a document using OCR.

        This method handles loading the document from either a cloud storage
        service (S3 or GCS) or a local path, and then performs OCR to extract
        text content using the `get_ocr` function.

        Args:
            file_path (str): Path to the document. This can be a cloud storage path or a local file path.

        Returns:
            dict: Dictionary containing the OCR results and metadata.

        Raises:
            ValueError: If the `source` is not "cloud" or "local".
        """
        logger.info("Starting text extraction using OCR...")

        # Load or download the document file
        if self.source == "cloud":
            fd, temp_file_path = tempfile.mkstemp()
            try:
                fd, temp_file = tempfile.mkstemp()
                temp_file_path = self.download_document(file_path, temp_file)
                logger.info(f"Successfully loaded document from {file_path}")
            finally:
                os.close(fd)  # Close the file descriptor
        elif self.source == "local":
            temp_file_path = file_path  # For local files, use the path directly
            logger.info(f"Successfully loaded document from local path {file_path}")
        else:
            raise ValueError("Invalid OCR source. Choose 'cloud' or 'local'.")

        # Handle PDF conversion and opening
        if os.path.splitext(file_path)[1].lower() != ".pdf":
            logger.info("Converting file to PDF")
            file_prefix = file_path
            temp_file_path = self.convert_doc_to_pdf(file_prefix=file_prefix, input_file=temp_file_path)

        result_dict = get_document_ocr(document_for_ocr=temp_file_path,
                                       markdown_output=self.markdown_output,
                                       llm_api_key=self.llm_api_key,
                                       target_size=self.target_size,
                                       page_range=self.page_range,
                                       timeout_minutes=self.timeout_minutes)

        result_dict["type"] = self.type
        result_dict["input"] = file_path

        # Clean up temporary file if it was downloaded
        if self.source == "cloud":
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Removed temporary file {temp_file_path}")

        return result_dict

    def load(self, input_path: str) -> dict:
        """
        Load and extract text content from ocr file.

        Args:
            input_path (str): A path to the ocr file.

        Returns:
            dict: A dictionary containing the extracted text and related metadata.
        """
        return self.get_text_from_document_ocr(file_path=input_path)