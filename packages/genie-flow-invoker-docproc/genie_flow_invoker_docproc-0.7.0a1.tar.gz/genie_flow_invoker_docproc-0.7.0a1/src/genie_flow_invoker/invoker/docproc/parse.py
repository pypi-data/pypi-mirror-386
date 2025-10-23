from http import HTTPStatus

from loguru import logger
from tika import parser

from genie_flow_invoker.doc_proc import RawDocumentFile, DocumentChunk, ChunkedDocument
from genie_flow_invoker.genie import GenieInvoker
from genie_flow_invoker.invoker.docproc.codec import (
    PydanticInputDecoder,
    PydanticOutputEncoder,
)
from genie_flow_invoker.utils import get_config_value
from genie_flow_invoker.invoker.docproc.backoff_caller import BackoffCaller


class DocumentParseInvoker(
    GenieInvoker,
    PydanticInputDecoder[RawDocumentFile],
    PydanticOutputEncoder[ChunkedDocument],
):
    """
    Parse a binary document into text and their metadata.
    """

    def __init__(
        self,
        tika_service_url: str,
        backoff_max_time=61,
        backoff_max_tries=10,
    ):
        self._tika_service_url = tika_service_url
        self._backoff_caller = BackoffCaller(
            TimeoutError,
            self.__class__,
            backoff_max_time,
            backoff_max_tries,
        )

    @classmethod
    def from_config(cls, config: dict):
        """
        The `meta.yaml` for the parser should contain the following properties:
        - tika_service_url: the url of the tika service
        - backoff_max_time: the maximum time in seconds between retries
        - backoff_max_tries: the maximum number of retries

        :param config: the dictionary of the configuration
        :return: a new instantiated invoker
        """
        tika_service_url = get_config_value(
            config,
            "TIKA_SERVICE_URL",
            "tika_service_url",
            "Tike Service URL",
            None,
        )
        if tika_service_url is None:
            raise ValueError("No tika service url provided")

        backoff_max_time = get_config_value(
            config,
            "TIKA_BACKOFF_MAX_TIME",
            "backoff_max_time",
            "Max backoff time (seconds)",
            61,
        )
        backoff_max_tries = get_config_value(
            config,
            "TIKA_MAX_BACKOFF_TRIES",
            "backoff_max_tries",
            "Max backoff tries",
            15,
        )

        return cls(
            tika_service_url=tika_service_url,
            backoff_max_time=backoff_max_time,
            backoff_max_tries=backoff_max_tries,
        )

    def invoke(self, content: str) -> str:
        input_document = self._decode_input(content)

        if input_document.document_data is None or input_document.document_data == "":
            logger.warning("received empty document with file name {}", input_document.filename)
            return self._encode_output(
                ChunkedDocument(
                    filename=input_document.filename,
                    document_metadata=dict(),
                    chunks=[],
                )
            )

        def parse():
            result = parser.from_buffer(
                input_document.byte_io,
                serverEndpoint=self._tika_service_url,
            )
            if result["status"] in [
                HTTPStatus.REQUEST_TIMEOUT,
                HTTPStatus.TOO_MANY_REQUESTS,
                HTTPStatus.INTERNAL_SERVER_ERROR,
            ]:
                logger.warning(
                    "Received status code {status_code}, from Tika",
                    status_code=result["status_code"],
                )
                raise TimeoutError()
            return result

        parsed_result = self._backoff_caller.call(parse)
        if "content" not in parsed_result or parsed_result["content"] is None:
            try:
                logger.warning(
                    "parsing obtained no content from Tika using parser {parser}",
                    parser=parsed_result.get("metadata").get("X-TIKA:Parsed-By"),
                )
            except KeyError:
                logger.error(
                    "parsing failed to obtained any content and "
                    "failed to retrieve metadata from Tika"
                )
            parsed_content = ""
        else:
            parsed_content = parsed_result["content"]

        chunk = DocumentChunk(
            content=parsed_content,
            original_span=(0, len(parsed_content)),
            hierarchy_level=0,
            parent_id=None,
        )
        chunked_document = ChunkedDocument(
            filename=input_document.filename,
            document_metadata=parsed_result["metadata"],
            chunks=[chunk],
        )
        return self._encode_output(chunked_document)
