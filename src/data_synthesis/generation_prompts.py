from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate


question_generator_system_message = SystemMessage(
    content="""You are a question generator.
    You are provided with some document from the ALICE O2 simulation documentation and the desired question difficulty.
    Your task is to think of a question that can be answered using only the information in this document.
    Easier questions should be more general and straightforward, while harder questions should be more specific and complex.
    Return only the generated question and nothing else."""
)

question_generator_prompt_template = PromptTemplate.from_template("""DOCUMENT:
    {document}
                    
    DIFFICULTY:
    {difficulty}
                   
    QUESTION:""")

answer_generator_system_message = SystemMessage(
    content="""You are a question answerer.
    You are provided with some document from the ALICE O2 simulation documentation and a question about it.
    Your task is to answer the question using only the information found in this document.
    Do not explain or mention the document, just use it to directly answer the question.
    The answer should be detailed, exhaustive and use different wording than the document.
    Return only the generated answer and nothing else."""
)

answer_generator_prompt_template = PromptTemplate.from_template("""DOCUMENT:
    {document}

    QUESTION:
    {question}

    ANSWER:""")


paraphraser_system_message = SystemMessage(
    content="""You are a document paraphraser.
    You are provided with a chunk of text from the ALICE O2 simulation documentation.
    Your task is to paraphrase this text.
    Try to use different wording and sentence structure, while keeping the same meaning and facts.
    The paraphrased text length should match the original text length.
    Return only the paraphrased document and nothing else."""
)

paraphraser_prompt_template = PromptTemplate.from_template("""DOCUMENT:
    {document}

    PARAPHRASED DOCUMENT:""")
