import time

from py4j.clientserver import logger


def write(df, file_format, mode, options,  path):
    start = time.time()
    logger.info("Writing to path : {0}".format(path))
    df_writer = df.write.format(file_format).mode(mode)
    for key in options:
        df_writer = df_writer.option(key, options[key])
    df_writer.save(path)
    logger.info("Time Taken to Write File : {}".format(time.time() - start))
