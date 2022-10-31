#!/bin/env python
import pandas
import torch
import typer
from datasets import Dataset
from rich.progress import Progress, SpinnerColumn, TextColumn, track
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
from transformers.pipelines.pt_utils import KeyDataset


def initial_pipeline(model_name):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return pipeline(task="text2text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    device=device)


app = typer.Typer()


@app.command()
def answer(
    question: str = typer.Argument(
        ...,
        help=
        "The question to answer"
    ),
    papers: str = typer.Argument(
        ...,
        help=
        "The tsv file of papers infomation with columns `title` and `abstract`"
    ),
    outfile: typer.FileTextWrite = typer.Argument(...),
    model: str = typer.Option("google/flan-t5-base"),
    batch_size: int = typer.Option(64, "--batch_size", "-bs")):
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
    ) as progress:
        progress.add_task(description="Loading Model...", total=None)
        pipe = initial_pipeline(model)
    df = pandas.read_csv(papers, sep='\t')
    inputs = df.apply(lambda x: f"{x['title']}\n{x['abstract']}\n\n{question}",
                      axis=1)
    data = KeyDataset(Dataset.from_pandas(inputs.to_frame()), key='0')
    answers = [
        output[0]['generated_text']
        for output in track(pipe(data, batch_size=batch_size),
                            total=inputs.size,
                            description="Reading...")
    ]
    outfile.write(f"{question}\n")
    outfile.write("\n".join(answers))


if __name__ == "__main__":
    app()
