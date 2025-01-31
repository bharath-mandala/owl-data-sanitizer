import argparse
import logging
from pyspark.sql import SparkSession

from spark_validation.common import DataFrameReader, DataFrameWriter
from spark_validation.common.config import Config
from spark_validation.common.constants import Constants
from spark_validation.dataframe_validation.dataframe_validator import DataframeValidator


class CreateHiveValidationDF:
    """Class to create validations tables."""

    logger = logging.getLogger(__name__)

    @staticmethod
    def validate(ss, config):
        """Apply validation process using config input file."""
        source_read_df = DataFrameReader \
            .jdbc(ss,
                  config.db_url,
                  config.db_user,
                  config.db_password,
                  config.source_df)

        comparable_dfs_list = [
            (t, DataFrameReader.jdbc(ss, config.db_url, config.db_user, config.db_password, config.source_df))
            for t in config.comparable_dfs_list]

        validator = DataframeValidator(
            spark=ss,
            source_df=source_read_df,
            id_col_name=config.id_col_name,
            correctness_rules_dict=config.correctness_rules_dict,
            parent_children_validation_pairs=config.parent_children_validation_pairs,
            completeness_rules_dic=config.completeness_rules_dic,
            comparable_dfs_list=comparable_dfs_list,
            unique_column_group_values_per_table=config.unique_column_group_values_per_table,
        )

        processed_df = validator.process()
        completeness_df = processed_df.limit(1).select(
            Constants.OVER_ALL_COUNT_COL,
            Constants.IS_ERROR_COL + Constants.OVER_ALL_COUNT_COL,
            Constants.DATE_TIME_REPORT_COL,
        )

        correctness_df = processed_df.drop(
            Constants.OVER_ALL_COUNT_COL,
            Constants.IS_ERROR_COL + Constants.OVER_ALL_COUNT_COL,
        )
        comparison_df = validator.compare()
        options = {"header": True,
                   "delimiter": ",",
                   "encoding": "UTF-8",
                   "nullValue": "null"}
        DataFrameWriter.write(correctness_df, "csv", "overwrite", options, config.output_correctness_table)

        DataFrameWriter.write(completeness_df, "csv", "overwrite", options, config.output_completeness_table)
        DataFrameWriter.write(comparison_df, "csv", "overwrite", options, config.output_comparison_table)


def main(args):
    """Run the main create table function using the sys arguments."""
    spark_session = SparkSession.builder \
        .appName("owl-data-sanitizer") \
        .master("local") \
        .config("spark.jars", args.jars) \
        .config("spark.driver.extraClassPath", args.jars) \
        .enableHiveSupport().getOrCreate()
    spark_session.conf.set("spark.sql.debug.maxToStringFields", "1000")
    spark_session.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
    spark_session.conf.set("mapreduce.fileoutputcommitter.algorithm.version", "2")
    arg_conf = spark_session.sparkContext.wholeTextFiles(args.config).collect()[0][1]
    config = Config.parse_text(arg_conf)

    CreateHiveValidationDF.validate(spark_session, config)


def create_parser():
    """Parse sys arguments and return parser object."""
    parser = argparse.ArgumentParser(description="Hive Validation")
    parser.add_argument(
        "-c", dest="config", action="store", help="config file", required=True,
    )
    parser.add_argument("-jars", dest="jars", action="store", help="Additional Jars", required=False)
    return parser


def init():
    """Wrap to make main call function testable by sending parsed arguments."""
    parser = create_parser()
    args = parser.parse_args()
    main(args)


if __name__ == "__main__":
    init()
