from langchain.docstore.document import Document
import boto3
import re


def clean_result(res_text):
    res = re.sub("\s+", " ", res_text).replace("...", "")
    return res


def get_top_n_results(resp, count):
    r = resp["ResultItems"][count]
    doc_title = r["DocumentTitle"]
    doc_uri = r["DocumentURI"]
    doc_excerpt = clean_result(r["Content"])
    combined_text = doc_excerpt
    return {"page_content": combined_text, "metadata": {"source": doc_uri, "title": doc_title, "excerpt": doc_excerpt}}


def kendra_query(kclient, kquery, kcount, kindex_id):
    response = kclient.retrieve(IndexId=kindex_id, QueryText=kquery.strip())
    if len(response["ResultItems"]) > kcount:
        r_count = kcount
    else:
        r_count = len(response["ResultItems"])
    docs = [get_top_n_results(response, i) for i in range(0, r_count)]
    return [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in docs]


def kendra_client(kindex_id, kregion):
    kclient = boto3.client('kendra', region_name=kregion)
    return kclient
