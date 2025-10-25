from langchain_core.language_models import BaseLanguageModel
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from typing import Optional, List, Union
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import BasePromptTemplate
from langchain_core.output_parsers.transform import BaseTransformOutputParser


class SummarizeStuff():
    """
    Containing Chain implemented for summarization of small texts

    Attributes:
        llm (BaseLanguageModel): Langchain language model.

    Methods: 
        get_summary(self, docs: Union[Document | List[Document]]) -> str:

    Example Usage (sync): 

    """

    def __init__(
            self, llm: BaseLanguageModel,
            map_prompt: Optional[BasePromptTemplate] = None,
            output_parser: Optional[BaseTransformOutputParser] = None) -> None:

        self.llm = llm
        # self.map_prompt = hub.pull("rlm/map-prompt")
        # self.output_parser = None

        if map_prompt:
            self.map_prompt = map_prompt
            # self.output_parser = custom_map_prompt[1]
        else:
            self.map_prompt = ChatPromptTemplate.from_messages(
                [("system", "Write a concise summary of the following (preserve language):\\n\\n{context}")])

        if output_parser:
            self.output_parser = output_parser
        else:
            self.output_parser = None

    def get_summary(self, docs: Union[Document | List[Document]]) -> str:
        chain = create_stuff_documents_chain(self.llm, self.map_prompt)
        if self.output_parser:
            chain |= self.output_parser
        result = chain.invoke({"context": docs})
        return result
