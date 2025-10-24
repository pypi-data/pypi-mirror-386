import base64
from typing import Any, Iterable, cast

import litellm
from rich.markdown import Markdown
from rich.panel import Panel

from .streaming import accumulate_streaming_text
from .task_stack import TaskStack

def system_prompt(page_nu, title, description, gists):

    giststring = ""
    if gists:
        gist_base = page_nu - len(gists)
        giststring = ("Here are the summaries of preceeding pages that you have access to. "
                      "Try not to repeat information from these")
        for index, gist in enumerate(gists):
            giststring += f"<gist page_nu={index + gist_base}>{gist}</gist>"

    descstring = ""
    if description:
        descstring = ("Here is a description of the document. "
                      "You MUST NOT repeat information that is already in this description. "
                      "Describe what is on your page, not overall document features."  
                      f"<description>{description}</description>")

    return ("You are an AI document summarizer. "
            "You will be given a one page PDF. "
            f"This PDF is page {page_nu} of a document titled {title}. "
            "You must accurately and concisely report the contents of this PDF using a single sentence. "
            "Your summary needs to be searchable, so include any important keywords that describe the content. "
            f"{descstring} {giststring}")

def summarize(gists,
              description,
              page_nu,
              title,
              page_bytes,
              model,
              tasks: TaskStack):
    # previous gists could supply additional context, but let's try it
    # context-free to start

    base64_string = base64.b64encode(page_bytes).decode("utf-8")

    response = litellm.completion(
            stream = True,
            model = model,
            messages = [ { 
               "role" : "system",
               "content": system_prompt(page_nu, title, description, gists)
             },
            {
                "role": "user",
                "content": [                    
                    {
                        "type": "text",
                        "text" : "Please summarize this page."
                    },
                    {
                        "type": "file",
                        "file":  {
                            "file_data": f"data:application/pdf;base64,{base64_string}"
                        },
                    },
                ],
            }])

    def render(current: str) -> None:
        tasks.render([Panel(Markdown(current))])

    return accumulate_streaming_text(response, render)
