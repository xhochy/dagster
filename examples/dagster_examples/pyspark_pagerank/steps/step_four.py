import re
from operator import add

from dagster_pyspark import SparkRDD, spark_session_resource

from dagster import InputDefinition, ModeDefinition, OutputDefinition, Path, pipeline, solid


def computeContribs(urls, rank):
    """Calculates URL contributions to the rank of other URLs."""
    num_urls = len(urls)
    for url in urls:
        yield (url, rank / num_urls)


def parseNeighbors(urls):
    """Parses a urls pair string into urls pair."""
    parts = re.split(r'\s+', urls)
    return parts[0], parts[1]


@solid(
    input_defs=[InputDefinition('pagerank_data', Path)], output_defs=[OutputDefinition(SparkRDD)]
)
def parse_pagerank_data_step_four(context, pagerank_data):
    lines = context.resources.spark.read.text(pagerank_data).rdd.map(lambda r: r[0])
    return lines.map(parseNeighbors)


@solid(input_defs=[InputDefinition('urls', SparkRDD)])
def rest_of_pipeline(context, urls):
    links = urls.distinct().groupByKey().cache()

    # Loads all URLs with other URL(s) link to from input file and initialize ranks of them to one.
    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 1.0))

    iterations = 2

    # Calculates and updates URL ranks continuously using PageRank algorithm.
    for _iteration in range(iterations):
        # Calculates URL contributions to the rank of other URLs.
        contribs = links.join(ranks).flatMap(
            lambda url_urls_rank: computeContribs(url_urls_rank[1][0], url_urls_rank[1][1])
        )

        # Re-calculates URL ranks based on neighbor contributions.
        ranks = contribs.reduceByKey(add).mapValues(lambda rank: rank * 0.85 + 0.15)

    # Collects all URL ranks and dump them to console.
    for (link, rank) in ranks.collect():
        context.log.info("%s has rank: %s." % (link, rank))

    return ranks.collect()


@pipeline(mode_defs=[ModeDefinition(resource_defs={'spark': spark_session_resource})])
def pyspark_pagerank_step_four():
    rest_of_pipeline(parse_pagerank_data_step_four())
