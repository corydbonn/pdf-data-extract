# Information Extraction from Historical PDF Files

## Overview: 

One of our researchers is interested in doing some historical economis research from an old document: [``THE UNIVERSAL BRITISH DIRECTORY OF Trade, Commerce, and Manufacture``](https://www.google.com/books/edition/The_Universal_British_Directory_of_Trade/UQwHAAAAQAAJ?hl=en). The document is available as a PDF file at [this link](https://books.google.com/books/download/The_Universal_British_Directory_of_Trade.pdf?id=UQwHAAAAQAAJ&output=pdf), but the content of the file is in a format that interleaves single column with multi-column layout (see for example, pages 4-6). The researcher would like to extract the data from the PDF and put it into a structured format (e.g. CSV, JSON, etc.) so that it can be analyzed.

## Objective:

Extract the text from the PDF, and put it in reading order. The multi-column layout should be converted to a single column of data, and parsed into a structured format so that it can be analyzed. For example, starting on page 4, the researcher would like to extract a list of name/profession pairs. The output should be a JSON file that looks something like this snippet:

```json
{
    "page": 4,
    "text_block": "Abbot is (by tradition) ſaid to have been confined and ſtarved ; near this gate, on the left, is another large gate, by which you enter the precincts of the monattery near the farm- houfe is a ftable fuppofed to have been the dormitory. [...]",
    "data": [
        {
            "name": "Samways Roddon, Eſq. ( F. )",
            "profession": "Clergy"
        },
        {
            "name": "Jenkins Rev. William",
            "profession": "Vicar"
        }
    ]
}
```

## Deliverables:

A ptyhon command line executable, that accepts a path to the PDF as an argument, and generates a JSON file that represents the document but allowing the structure to be recovered as per the objective outline above.

You may also generate a Jupyter notebook that demonstrates your approach to the problem. We will be evaluating your approach, so please include any notes that you think will help us understand your thought process. If you use a service like ChatGPT, please include the API calls in your code, i.e., the workflow should not consist of manual steps that wouldn't scale to a large number of documents.