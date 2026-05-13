# ---
# jupyter:
#   jupytext:
#     comment_magics: false
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% id="ofZHOerGBTx8"
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# %% [markdown] id="0kIyAXORBTx9"
# # Evaluating Multimodal Image Search
# *powered by BigQuery, Vertex AI and Gemini*
#
# This notebook builds upon the multimodal analysis, search, and understanding capabilities established in [Part 1](./part_1_multimodal_analysis_search.ipynb) and [Part 2](./part_2_large_scale_understanding.ipynb). Here, we focus on evaluating the performance of the image search functionality which uses BigQuery and Gemini. We will leverage the same tables, models and vector search created in the previous notebook to assess the accuracy of our semantic search. We will use [DeepEval](https://docs.confident-ai.com/), the open-source LLM evaluation framework, to set up and execute our test cases and calculate the different evaluation metrics (detailed below).
#
# This notebook will cover:
#
# - **Defining evaluation metrics for document retrieval**: We will cover relevant metrics to evaluate the image search, i.e. our vector search-backed document retrieval. Metrics such as contextual recall and precision, will assess how well the system retrieves relevant images given a textual query. We will use a diverse set of natural language queries related to common bus stop issues (e.g., "damaged bench," "litter near shelter," "graffiti on the wall") as our test cases.
#
# - **Using Gemini as multimodal LLM judge in DeepEval evaluations**: We will leverage Gemini 1.5 Pro to evaluate each retrieved image and determine whether it's a true or false positive. These results will be used to calculate the document retrieval metrics. Using LLM for evaluation of retrieved documents is necessary since there's no labeled dataset, as is often the case.
#
# For our image search use case, this evaluation will help answer the following questions:
#
# 1. Do the vector embeddings meaningfully represent the bus stop images and accurately capture the cleanliness/maintenance/safety nuances?
# 	- This is influenced by hyperparameters like the choice of **embedding model**, **prompt**, and **temperature**.
# 2. Does the vector search retrieve the relevant results and rerank them in the right order?
# 	- This is influenced by hyperparameters like search parameters **top-K**, **distance type**, and **reranking** logic.
#
# This quantitative assessment provides valuable insights into the strengths of multimodal image search, along with actionable results to tune the aforementioned hyperparameters. The methods described here can be readily applied to other document retrieval systems, be it standalone like a search application or a part of a RAG pipeline for a LLM application.

# %% [markdown] id="WzI1RC8NnJT5"
# ### Why does document retrieval evaluation matter?

# %% [markdown] id="mJog9DT5nfJS"
# Evaluating document retrieval is crucial for both search applications and Retrieval-Augmented-Generation (RAG) pipelines because it directly impacts the quality and relevance of the information retrieved. Effective evaluation helps identify areas for improvement in retrieval systems, leading to more accurate, comprehensive, and satisfactory search results and LLM-generated responses.

# %% [markdown] id="pDGx79sanO3Y"
# In the context of RAG, you typically evaluate the Retriever and Generator separately to help pinpoint issues in your RAG pipeline. The following diagram shows the relevant metrics for each component. In this notebook, we focus on the Retriever metrics.

# %% [markdown] id="6u9QIm7vuWPY"
# <div style="text-align: center;">
#   <img src="https://d2lsxfc3p6r9rv.cloudfront.net/rag-pipeline.svg" alt="RAG pipeline evaluation" width="300px" style="margin: auto;display: block;margin-left: auto;margin-right: auto;">
#   <p>RAG pipeline evaluation - Source: https://docs.confident-ai.com/docs/guides-rag-evaluation</p>
# </div>

# %% [markdown] id="AFqQKMnW9HJt"
# Using DeepEval and Gemini as LLM judge, we will specifically measure the following metrics for a comprehensive evaluation of our image search:
# - **Contextual recall** which calculates the percentage of relevant images out of all retrieved images. This metric evaluates the ability of the underlying embedding model to accurately capture and retrieve as many relevant images based on the textual query. For more details on how it is calculated, see [multimodal contextual recall](https://docs.confident-ai.com/docs/multimodal-metrics-contextual-recall#how-is-it-calculated).
# - **Contextual precision** which evaluates the order of the retrieved images where the relevant images rank higher than the irrelevant ones. For more details on how it is calculated, see [multimodal contextual precision](https://docs.confident-ai.com/docs/multimodal-metrics-contextual-precision#how-is-it-calculated).
#
# Note: You might have noticed we are not measuring **contextual relevancy**. While contextual recall compares retrieved documents against expected output, contextual relevancy compares retrieved documents against user input. They're both useful for evaluating a general RAG retriever. However, in the case of a simple search application, user input and expected output are semantically equivalent (e.g. querying for 'broken glass' has the expected output of 'broken glass' images). Therefore, contextual relevancy and recall are 100% the same in the case of a search application like our cross-modality image search use case.

# %% [markdown] id="jbmv2fBEUN51"
# ## Prerequisites
#
#

# %% [markdown] id="IhVqAbHbZPd6"
# Since this notebook builds on parts 1 and 2, it is assumed you have already processed the image batches. Specifically, in this notebook, you will use the following pre-deployed BigQuery and Cloud Storage resources:
#
# - Image reports table `multimodal.image_reports`
# - Image vector embeddings table `multimodal.image_reports_vector_db`
# - Remote text embedding model `multimodal.text_embedding_model`
# - Cloud resource connection `multimodal.{REGION}.multimodal`
# - Cloud Storage bucket and pre-processed images under `gs://{PROJECT_ID}-multimodal/target/*`

# %% [markdown] id="ijFFC4kaBTx_"
# #### Cost considerations

# %% [markdown] id="4xtQm6u_BTx_"
# While no new cloud resources will be created in this notebook, running this notebook will incur minor costs associated with Gemini API usage and BigQuery processing. The DeepEval framework evaluates the accuracy of BigQuery vector search results, and is configured to use Gemini 1.5 Pro as the LLM judge for the few test cases defined below. Refer to the following pages for pricing details of the Cloud services used in this notebook:
#
# - [BigQuery pricing](https://cloud.google.com/bigquery/docs/pricing)
# - [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

# %% [markdown] id="kq5CVnCXebOb"
# ## Getting Started

# %% [markdown] id="77mCQO2Of15N"
# Let's first create some environment variables, including your Google Cloud project ID and the region where you previously deployed the prerequisite resources into:

# %% id="HR__Ef43ZPfQ"
PROJECT_ID = "your-project-id" # @param {type:"string"}
REGION = "us-central1" # @param {type:"string"}

BUCKET_NAME = f"{PROJECT_ID}-multimodal"  # Bucket pre-created
IMAGE_PATH = f"gs://{BUCKET_NAME}/target" # Path of pre-processed images

# %% [markdown] id="n8rxPY7tZY5U"
# ### Install packages

# %% id="Q1eNnfaqZTNd"
%pip install --upgrade --user --quiet \
    google-cloud-aiplatform \
    google-cloud-bigquery \
    deepeval

# %% [markdown] id="eUHDKyrvZbfY"
# ### Import libraries

# %% id="uj6OAruUmS45"
from google.cloud import bigquery
import asyncio
import vertexai
import pandas as pd
from IPython.display import HTML

# %% id="wtkyjl75afM-"
# initialize bigquery client
client = bigquery.Client()

# set pandas styling options
# Don't truncate strings in BigQuery query results
pd.set_option('display.max_colwidth', None)


# %% [markdown] id="k4_Ja4irfhVf"
# ### Define utility functions

# %% [markdown] id="60Pkxw0VfmLV"
# As per prior notebook, let's define some styling functions to help display dataframes with embedded images.

# %% id="INZg3gfPfkyZ"
# Generate HTML img tag from signed url
def preview_image(uri):
  if pd.notna(uri):
    return f'<img src="{uri}" style="width:300px; height:auto; transition: transform 0.25s ease; border: 1px solid black;" onmouseover="this.style.transform=\'scale(2.5)\';" onmouseout="this.style.transform=\'scale(1.0)\';">'
  else:
    return None


# %% [markdown] id="VI0xLxmm7HBa"
# ## Preview Image Dataset

# %% [markdown] id="rIDOBrKegaN_"
# Let's first confirm the image reports and embeddings tables are already populated.

# %% [markdown] id="puoEjIY8iL4m"
# If you've completed part 1, there should be 70+ pre-processed images and corresponding vector embeddings in BigQuery. It's a small dataset, but sufficient to run some searches and evaluate initial search quality.

# %% id="bIw82qhuHWy0"
%%bigquery image_reports_df
SELECT * FROM `multimodal.image_reports`

# %% id="cNWTTydb7jkl"
len(image_reports_df)

# %% id="DTDpz3Rx7El4"
%%bigquery image_embeddings_df
SELECT * FROM `multimodal.image_reports_vector_db`

# %% id="POm3f4NLidsJ"
len(image_embeddings_df)

# %% [markdown] id="YCrM4k-NkdSy"
# Let's preview some of these image reports

# %% id="itFJzBFNr72l"
image_reports_df.head()


# %% [markdown] id="HWmaBmF5m7wk"
# ## Set up Document Retriever

# %% [markdown] id="lQZRgFEwkxP3"
# We're using BigQuery `VECTOR_SEARCH` to power our document (image) retriever.
# To faciliate the retrieval, we'll wrap the BigQuery SQL logic in a search helper function as we did in prior notebook.

# %% [markdown] id="WV_sH-wSFyd-"
# ### Define search helper function

# %% [markdown] id="zP4TMXJaoq8_"
# Let's define this utility function for semantic search. This function generates the text embedding for the test query using the same `text_embedding_model` (and same task type), then runs the `VECTOR_SEARCH` query against the base table of embeddings for the vectors, that is `reports_vector_db` table. It then appends the authenticated url link to preview the results including the image.

# %% id="bz-RnhB921xi"
def run_semantic_search(query:str, top_k:int):
  escaped_query = query.replace("'", "''").replace("\\", "\\\\")

  search_terms_embeddings_query = f"""
    SELECT
      query.content AS search, distance,
      RANK() OVER (ORDER BY distance ASC) as rank,  -- Calculate rank based on distance
      base.report_id, base.bus_stop_id, base.uri, base.description,
      CONCAT("https://storage.mtls.cloud.google.com/", SPLIT(base.uri, "gs://")[OFFSET(1)]) AS url,
      base.cleanliness_level, base.safety_level
    FROM
      VECTOR_SEARCH(
        TABLE `multimodal.image_reports_vector_db`,
        'embedding',
        (
          SELECT * FROM ML.GENERATE_EMBEDDING(
          MODEL `multimodal.text_embedding_model`,
          (
            SELECT '{escaped_query}' AS content
          ),
          STRUCT('SEMANTIC_SIMILARITY' as task_type))
        ),
        top_k => {top_k},
        distance_type => 'COSINE'
      )
  """

  return client.query(search_terms_embeddings_query).to_dataframe()


# %% [markdown] id="H7hMgttCoApZ"
# ### Run retriever

# %% [markdown] id="Ja4Op-athYy-"
# Let's test our retriever using the query "broken glass":

# %% id="7c8xtt1QhbPV"
query = "broken glass"
top_k = 3
retrieved_docs_df = run_semantic_search(query, top_k)

retrieved_docs_df['image'] = retrieved_docs_df['url'].apply(preview_image)

# Display the DataFrame with embedded images
HTML(retrieved_docs_df.sort_values('rank')[['bus_stop_id', 'uri', 'rank', 'image', 'description']].to_html(escape=False))

# %% [markdown] id="nfpEzfLiBTyD"
# The retrieved images should all have broken glass, as shown in the output screenshot below. Note the underlying search is done against the actual image description embeddings, and does not take into account the image file name.

# %% [markdown] id="FRtdBIzEBTyD"
# ![search results to broken glass query](../docs/images/nb2-run-retriever.png)

# %% [markdown] id="4YzIjJJAarf9"
# ## Set up DeepEval to use Vertex AI

# %% [markdown] id="LnSMxWUje9e7"
# ### Define Gemini as multimodal evaluation model

# %% id="Pl7SPDFnaTLs"
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part, Image, HarmCategory, HarmBlockThreshold
from deepeval.models.base_model import DeepEvalBaseMLLM
from deepeval.test_case import MLLMImage
from pydantic import BaseModel
from typing import Optional, List, Dict, Tuple, Union

class MultimodalGoogleVertexAI(DeepEvalBaseMLLM):
    """Class that implements Vertex AI for DeepEval"""
    def __init__(self, model_name, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)
        self.model = self.load_model(*args, **kwargs)

    def load_model(self, *args, **kwargs):
        # Initialize safety filters for Vertex AI model
        # This is important to ensure no evaluation responses are blocked
        safety_settings = {
            HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
        }

        vertexai.init(project=kwargs['project'], location=kwargs['location'])

        return GenerativeModel(
            model_name=self.model_name,
            safety_settings=safety_settings)

    def generate_prompt(
        self, multimodal_input: List[Union[str, MLLMImage]] = []
    ):
        prompt = []
        for ele in multimodal_input:
            if isinstance(ele, str):
                prompt.append(ele)
            elif isinstance(ele, MLLMImage):
                if ele.local == True:
                    image = Part.from_image(Image.load_from_file(ele.url))
                else:
                    image = Part.from_uri(uri=ele.url, mime_type="image/jpeg")

                prompt.append(image)
            else:
                raise ValueError(f"Invalid input type: {type(ele)}")

        return prompt

    def generate(
        self, multimodal_input: List[Union[str, MLLMImage]], schema: Optional[BaseModel] = None
    ) -> Tuple[str, float]:

        prompt = self.generate_prompt(multimodal_input)
        if schema is not None:
            response = self.model.generate_content(prompt, generation_config=GenerationConfig(
                response_mime_type="application/json", response_schema=schema
            ))
        else:
            response = self.model.generate_content(prompt)

        return response.text

    async def a_generate(
        self, multimodal_input: List[Union[str, MLLMImage]], schema: Optional[BaseModel] = None
    ) -> Tuple[str, float]:
        prompt = self.generate_prompt(multimodal_input)
        if schema is not None:
            response = await self.model.generate_content_async(prompt, generation_config=GenerationConfig(
                response_mime_type="application/json", response_schema=schema
            ))
        else:
            response = await self.model.generate_content_async(prompt)

        return response.text

    def get_model_name(self) -> str:
        return self.model_name



# %% [markdown] id="SiNOCGRUdqsr"
# Let's instantiate the Vertex AI wrapper class to use Gemini 1.5 Pro for evaluating metrics criteria in subsequent section.

# %% id="e8FcqtB_dzcy"
gemini_pro = MultimodalGoogleVertexAI(
    model_name="gemini-1.5-pro-001",
    project=PROJECT_ID,
    location=REGION
)

# %% [markdown] id="rmsT9IIEp4Yt"
# ### Evaluate sample test case

# %% [markdown] id="_asJpjvmqUS7"
# Let's go back to our image search results from "broken glass" query where we got 3 correctly identified broken glass images. Before we measure the recall and precision, let's add one false positive image `MA-01.jpg` for testing purposes:

# %% id="KAl-umMh02El"
retrieved_docs = retrieved_docs_df.sort_values('rank')['uri'].values.tolist()
retrieved_docs.append(f"{IMAGE_PATH}/MA-01.jpg")
retrieved_docs

# %% [markdown] id="ciLz2ZmsBTyE"
# The `retrieved_docs` list should contain 4 images including the last one we just manually appended:

# %% [markdown] id="KXXFSQCLBTyE"
# ![list of image uris for our first test run](../docs/images/nb2-evaluate-sample-test-case1.png)

# %% [markdown] id="g44ReJyr2Oyb"
#  Given there are 4 images, with the first 3 being relevant and the last is non-relevant, we should see the following results:
#  - contextual recall should be equal to 3/4 = 0.75
#  - contextual precision should be equal to 1 since all relevant images rank higher

# %% id="9ubcKnbTz16O"
from deepeval.test_case import MLLMTestCase, MLLMImage
from deepeval.metrics import MultimodalContextualRecallMetric, MultimodalContextualPrecisionMetric

test_case = MLLMTestCase(
    input=["broken glass"],
    actual_output = [],
    expected_output=[f"Node {i} image shows broken glass in or around the sidewalk" for i in enumerate(retrieved_docs)],
    retrieval_context=[MLLMImage(uri) for uri in retrieved_docs]
)

recall_metric = MultimodalContextualRecallMetric(model=gemini_pro)
precision_metric = MultimodalContextualPrecisionMetric(model=gemini_pro)

print("Evaluating Contextual Recall:")
recall_metric.measure(test_case)
print("Score: ", recall_metric.score)
print("Reason: ", recall_metric.reason)
for verdict in recall_metric.verdicts: print(verdict)

print("Evaluating Contextual Precision:")
precision_metric.measure(test_case)
print("Score: ", precision_metric.score)
print("Reason: ", precision_metric.reason)
for verdict in precision_metric.verdicts: print(verdict)

# %% [markdown] id="2XDRN2znBTyE"
# ![evaluation metrics of sample test case](../docs/images/nb2-evaluate-sample-test-case2.png)

# %% [markdown] id="lA7lWT3Xobfx"
# ## Define Multiple Test Cases

# %% [markdown] id="X4kakQh6gLFm"
# Let's create a helper function which we'll use to create several LLM test cases given different queries.

# %% id="fTe9m28Fdrfh"
from deepeval.test_case import MLLMTestCase, MLLMImage

def create_llm_test_case(query: str, top_k: int) -> MLLMTestCase:
    """
    Creates MLLMTestCase given textual query and top_k arguments

    Args:
        query: textual query to execute.
        top_k: The number of top results to consider.

    Returns:
        A MLLMTestCase object
    """
    print(f"Creating new test case: search {top_k} '{query}' images")
    # Run semantic search and retrieve documents
    retrieved_docs_df = run_semantic_search(query, top_k)
    retrieved_docs = retrieved_docs_df.sort_values('rank')['uri'].values.tolist()
    print('\n'.join(map(str, retrieved_docs)))

    # Create test case comparing retrieved documents against expected documents attributes
    test_case = MLLMTestCase(
      input=[query],
      actual_output = [],
      # expected_output=[f"The image shows noticeable amount of ${query}"] * len(retrieved_docs),
      expected_output=[f"Node {i} image shows ${query} in or around the sidewalk" for i in enumerate(retrieved_docs)],
      retrieval_context=[MLLMImage(uri) for uri in retrieved_docs]
    )

    return test_case


# %% [markdown] id="SkFq6Ms6mhMx"
# Now let's generate different test cases for the following sample searches:
# - broken glass
# - damaged bench
# - excessive litter
# - graffiti
#
# This will run the different searches and store the results for subsequent metrics calculation.

# %% id="g_o6WJ-kmZKP"
queries = ["broken glass", "damaged bench", "excessive litter", "graffiti"]
top_k = 3
test_cases = [create_llm_test_case(query, top_k) for query in queries]

# %% [markdown] id="9xcy48JaBTyF"
# You should expect an output as follows, including the list of retrieved image uris for each test case.

# %% [markdown] id="JZT00OGHBTyF"
# ![create and run test cases screenshot](../docs/images/nb2-define-test-cases.png)

# %% [markdown] id="wZnHqNAVoXU7"
# ## Calculate Metrics

# %% [markdown] id="kiCLXlnaBTyF"
# As mentioned above, measuring both contextual recall and precision allows us to comprehensively evaluate the accuracy of our semantic search.

# %% [markdown] id="igEvnDU9j35p"
# ### Measure Contextual Recall

# %% id="p4NZkKVnnPQu"
from deepeval.metrics import MultimodalContextualRecallMetric

recall_metric = MultimodalContextualRecallMetric(model=gemini_pro)
avg_recall = 0

# Measure metric for each test_case and display corresponding score and reason
# Uncomment vertdicts line to include verdict for each retrieved document.
for test_case in test_cases:
  print("Query:", test_case.input[0])
  # print("Retrieved Images:", test_case.retrieval_context)
  recall_metric.measure(test_case)
  print("Score: ", recall_metric.score)
  print("Reason: ", recall_metric.reason)
  avg_recall += recall_metric.score
  # for verdict in recall_metric.verdicts: print(verdict)
  print("\n")

avg_recall = avg_recall / len(test_cases)
print(f"Average Contextual Recall: {avg_recall}")

# %% [markdown] id="JZnRGTzDBTyF"
# Here are sample results. In this case, the search shows perfect contextual recall for all test cases. Due to probabilistic nature of LLM evaluations, you may sporadically get slightly different results.

# %% [markdown] id="7frKUvNvBTyF"
# ![contextual recall sample results](../docs/images/nb2-measure-contextual-recall.png)

# %% [markdown] id="dm6j0ZjilosP"
# ### Measure Contextual Precision

# %% id="9OmMkuMnlmeS"
from deepeval.metrics import MultimodalContextualPrecisionMetric

precision_metric = MultimodalContextualPrecisionMetric(model=gemini_pro)
avg_precision = 0

# Measure metric for each test_case and display corresponding score and reason
# Uncomment vertdicts line to include verdict for each retrieved document.
for test_case in test_cases:
  print("Query:", test_case.input[0])
  # print("Retrieved Images:", test_case.retrieval_context)
  precision_metric.measure(test_case)
  print("Score: ", precision_metric.score)
  print("Reason: ", precision_metric.reason)
  avg_precision += precision_metric.score
  # for verdict in precision_metric.verdicts: print(verdict)
  print("\n")

avg_precision = avg_precision / len(test_cases)
print(f"Average Contextual Precision: {avg_precision}")

# %% [markdown] id="w4VYpkbtBTyG"
# Below are sample results. Due to probabilistic nature of LLM evaluations, you may sporadically get slightly different results.

# %% [markdown] id="Bu9zVdUjBTyG"
# ![contextual precision sample results](../docs/images/nb2-measure-contextual-precision.png)

# %% [markdown] id="hnqRVV8e5LDn"
# ## Summary

# %% [markdown] id="3KxznYfe5R9U"
# In this notebook, we evaluated a multimodal image search system using DeepEval and Gemini 1.5 Pro as an LLM judge. Contextual recall and precision metrics demonstrated the effectiveness of Gemini vector embeddings and BigQuery vector search in retrieving relevant images based on textual queries. While the initial results showed high accuracy, further improvements could focus on expanding the dataset and test cases for more robust evaluation. More complex queries could be added and different embedding models and search parameters (e.g., top-k, distance type, filtering/reranking logic) including hybrid search could be explored to further improve retrieval quality. The [DeepEval framework](https://docs.confident-ai.com/) and [Vertex AI Gemini API](https://cloud.google.com/vertex-ai/generative-ai/docs/overview) provided crucial tools for this evaluation.
#
# While this notebook focused on retrieval quality of BigQuery vector search, future work could also include retrieval cost and performance (latency, throughput) analysis to provide a complete evaluation of the system's efficacy and scalability, leveraging BigQuery vector index and batch processing. Refer to this [guide](https://medium.com/google-cloud/bigquery-vector-search-a-practitioners-guide-0f85b0d988f0) for more details about scaling BigQuery vector search.

# %% [markdown] id="AGyrOPFJBTyG"
#
