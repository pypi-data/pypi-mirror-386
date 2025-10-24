import asyncio
import logging
from datetime import datetime

from forecasting_tools.ai_models.ai_utils.ai_misc import clean_indents
from forecasting_tools.ai_models.exa_searcher import (
    ExaHighlightQuote,
    ExaSearcher,
    SearchInput,
)
from forecasting_tools.ai_models.general_llm import GeneralLlm
from forecasting_tools.ai_models.model_interfaces.ai_model import AiModel
from forecasting_tools.ai_models.model_interfaces.outputs_text import OutputsText
from forecasting_tools.helpers.works_cited_creator import WorksCitedCreator
from forecasting_tools.util.misc import fill_in_citations, make_text_fragment_url

logger = logging.getLogger(__name__)


class SmartSearcher(OutputsText, AiModel):
    """
    Answers a prompt, using search results to inform its response.
    """

    def __init__(
        self,
        include_works_cited_list: bool = False,
        use_brackets_around_citations: bool = False,
        num_searches_to_run: int = 2,
        num_sites_per_search: int = 10,
        model: str | GeneralLlm = "gpt-4.1",
        temperature: float | None = None,
        use_advanced_filters: bool = False,
    ) -> None:
        assert (
            temperature is None or 0 <= temperature <= 1
        ), "Temperature must be between 0 and 1"
        self.temperature = temperature
        self.num_quotes_to_evaluate_from_search = 15
        self.number_of_searches_to_run = num_searches_to_run
        self.exa_searcher = ExaSearcher(
            include_text=False,
            include_highlights=True,
            num_results=num_sites_per_search,
        )
        if isinstance(model, str):
            self.llm = GeneralLlm(model=model, temperature=temperature)
        else:
            logger.warning(
                "SmartSearcher: Temperature not used if model is a preconfigured GeneralLlm"
            )
            self.llm = model
        self.include_works_cited_list = include_works_cited_list
        self.use_citation_brackets = use_brackets_around_citations
        self.use_advanced_filters = use_advanced_filters

    async def invoke(self, prompt: str) -> str:
        logger.debug(f"Running search for prompt: {prompt}")
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        report, _ = await self._mockable_direct_call_to_model(prompt)
        logger.debug(f"Report: {report[:1000]}...")
        return report

    async def _mockable_direct_call_to_model(
        self, prompt: str
    ) -> tuple[str, list[ExaHighlightQuote]]:
        search_terms = await self.__come_up_with_search_queries(prompt)
        quotes = await self.__search_for_quotes(search_terms)
        report = await self.__compile_report(quotes, prompt)
        if self.include_works_cited_list:
            works_cited_list = WorksCitedCreator.create_works_cited_list(quotes, report)
            report = report + "\n\n" + works_cited_list
        final_report = self.__add_links_to_citations(report, quotes)
        return final_report, quotes

    async def __come_up_with_search_queries(self, prompt: str) -> list[SearchInput]:
        if self.use_advanced_filters:
            return await self.__create_search_queries_with_filters(prompt)
        else:
            return await self.__create_basic_search_queries(prompt)

    async def __create_basic_search_queries(self, prompt: str) -> list[SearchInput]:
        prompt = clean_indents(
            f"""
            You have been given the following instructions. Instructions are included between <><><><><><><><><><><><> tags.

            <><><><><><><><><><><><>
            {prompt}
            <><><><><><><><><><><><>

            Generate {self.number_of_searches_to_run} google searches that will help you fulfill any questions in the instructions.
            Make them each target different aspects of the question.
            Please provide the searches as a list of strings like this:
            ["search 1", "search 2"]
            Give no other text than the list of search terms.
            """
        )
        search_terms = await self.llm.invoke_and_return_verified_type(prompt, list[str])
        logger.debug(f"Decided on searches: {search_terms}")
        search_inputs = [
            self.exa_searcher.string_to_default_search_input(search_term)
            for search_term in search_terms
        ]
        return search_inputs

    async def __create_search_queries_with_filters(
        self, prompt: str
    ) -> list[SearchInput]:
        prompt = clean_indents(
            f"""
            You have been given the following instructions. Instructions are included between <><><><><><><><><><><><> tags.

            <><><><><><>START INSTRUCTIONS<><><><><><>
            {prompt}
            <><><><><><>END INSTRUCTIONS<><><><><><>

            Generate {self.number_of_searches_to_run} google searches that will help you fulfill any questions in the instructions.
            Consider and walk through the following before giving your json answers:
            - What are some possible search queries and strategies that would be useful?
            - What are the aspects of the question that are most important? Are there multiple aspects?
            - Where is the information you need likely to be found or what will good sources likely contain in them?
            - Would it already be at the top of the search results, or should you filter for it?
            - What filters would help you achieve this to increase the information density of the results?
            - You have limited searches, which approaches would be highest priority?
            Please only use the additional search fields ONLY IF it would return useful results.
            Don't unnecessarily constrain results.
            Remember today is {datetime.now().strftime("%Y-%m-%d")}.

            {self.llm.get_schema_format_instructions_for_pydantic_type(SearchInput)}

            Make sure to return a list of the search inputs as a list of JSON objects in this schema.
            This should be a list, not a dict that contains a list. The list can be of one item.
            """
        )
        search_terms = await self.llm.invoke_and_return_verified_type(
            prompt, list[SearchInput]
        )
        search_log = "\n".join(
            [f"Search {i+1}: {search}" for i, search in enumerate(search_terms)]
        )
        logger.info(f"Decided on searches:\n{search_log}")
        return search_terms

    async def __search_for_quotes(
        self, search_inputs: list[SearchInput]
    ) -> list[ExaHighlightQuote]:
        all_quotes: list[list[ExaHighlightQuote]] = await asyncio.gather(
            *[
                self.exa_searcher.invoke_for_highlights_in_relevance_order(search)
                for search in search_inputs
            ]
        )
        flattened_quotes = [quote for sublist in all_quotes for quote in sublist]
        unique_quotes: dict[str, ExaHighlightQuote] = {}
        for quote in flattened_quotes:
            if quote.highlight_text not in unique_quotes:
                unique_quotes[quote.highlight_text] = quote
        deduplicated_quotes = sorted(
            unique_quotes.values(), key=lambda x: x.score, reverse=True
        )

        if len(deduplicated_quotes) < self.num_quotes_to_evaluate_from_search:
            logger.warning(
                f"Couldn't find the number of quotes asked for. Found {len(deduplicated_quotes)} quotes, but need {self.num_quotes_to_evaluate_from_search} quotes"
            )
        most_relevant_quotes = deduplicated_quotes[
            : self.num_quotes_to_evaluate_from_search
        ]
        return most_relevant_quotes

    async def __compile_report(
        self,
        search_results: list[ExaHighlightQuote],
        original_instructions: str,
    ) -> str:
        if len(search_results) == 0:
            return (
                "No search results found for the query using the search filter chosen"
            )

        assert (
            len(search_results) <= self.num_quotes_to_evaluate_from_search
        ), "Too many search results found"

        search_result_context = self.__turn_highlights_into_search_context_for_prompt(
            search_results
        )
        logger.info(f"Generating response using {len(search_results)} quotes")
        logger.debug(f"Search results:\n{search_result_context}")
        prompt = clean_indents(
            f"""
            Today is {datetime.now().strftime("%Y-%m-%d")}.
            You have been given the following instructions. Instructions are included between <><><><><><><><><><><><> tags.

            <><><><><><><><><><><><>
            {original_instructions}
            <><><><><><><><><><><><>


            After searching the internet, you found the following results. Results are included between <><><><><><><><><><><><> tags.
            <><><><><><><><><><><><>
            {search_result_context}
            <><><><><><><><><><><><>

            Please follow the instructions and use the search results to answer the question. Unless the instructions specifify otherwise, please cite your sources inline and use markdown formatting.

            For instance, this quote:
            > [1] "SpaceX successfully completed a full flight test of its Starship spacecraft on April 20, 2023"

            Would be cited like this:
            > SpaceX successfully completed a full flight test of its Starship spacecraft on April 20, 2023 [1].
            """
        )
        report = await self.llm.invoke(prompt)
        return report

    @staticmethod
    def __turn_highlights_into_search_context_for_prompt(
        highlights: list[ExaHighlightQuote],
    ) -> str:
        search_context = ""
        for i, highlight in enumerate(highlights):
            url = highlight.source.url
            title = highlight.source.title
            publish_date = highlight.source.readable_publish_date
            search_context += f'[{i+1}] "{highlight.highlight_text}". [This quote is from {url} titled "{title}", published on {publish_date}]\n'
        return search_context

    def __add_links_to_citations(
        self, report: str, highlights: list[ExaHighlightQuote]
    ) -> str:
        urls_for_citations = []
        for i, highlight in enumerate(highlights):
            url = highlight.source.url
            if url is None:
                url = "No URL found"
                logger.warning(f"Highlight {i} has no url")
            text_fragment_url = make_text_fragment_url(highlight.highlight_text, url)
            urls_for_citations.append(text_fragment_url)
        report = fill_in_citations(
            urls_for_citations, report, self.use_citation_brackets
        )

        return report

    @staticmethod
    def _get_cheap_input_for_invoke() -> str:
        return "What is the recent news on SpaceX?"

    @staticmethod
    def _get_mock_return_for_direct_call_to_model_using_cheap_input() -> str:
        return "Mock Report: Pretend this is an extensive report"
