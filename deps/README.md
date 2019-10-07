Batteries Included
==========

To download the dependencies for most DLJC tools (excluding the Checker Framework),
run `bash fetch_dependencies.sh`, then set your `DAIKONDIR` environment variable 
to `/path/to/tools/daikon-src`.

To download a corpus of sample projects, run `python fetch_corpus.py`

Then, invoke dljc in a project directory with 

    dljc -l <thisdir>/libs -t <tools> -- <build cmd>
