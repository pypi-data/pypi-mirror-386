from abc import abstractmethod

from shai_plugin.entities.model import ModelType
from shai_plugin.entities.model.rerank import RerankResult
from shai_plugin.interfaces.model.ai_model import AIModel


class RerankModel(AIModel):
    """
    Base Model class for rerank model.
    """

    model_type: ModelType = ModelType.RERANK

    ############################################################
    #        Methods that can be implemented by plugin         #
    ############################################################

    @abstractmethod
    def _invoke(
        self,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: float | None = None,
        top_n: int | None = None,
        user: str | None = None,
    ) -> RerankResult:
        """
        Invoke rerank model

        :param model: model name
        :param credentials: model credentials
        :param query: search query
        :param docs: docs for reranking
        :param score_threshold: score threshold
        :param top_n: top n
        :param user: unique user id
        :return: rerank result
        """
        raise NotImplementedError

    ############################################################
    #                 For executor use only                    #
    ############################################################

    def invoke(
        self,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: float | None = None,
        top_n: int | None = None,
        user: str | None = None,
    ) -> RerankResult:
        """
        Invoke rerank model

        :param model: model name
        :param credentials: model credentials
        :param query: search query
        :param docs: docs for reranking
        :param score_threshold: score threshold
        :param top_n: top n
        :param user: unique user id
        :return: rerank result
        """

        with self.timing_context():
            try:
                return self._invoke(model, credentials, query, docs, score_threshold, top_n, user)
            except Exception as e:
                raise self._transform_invoke_error(e) from e
