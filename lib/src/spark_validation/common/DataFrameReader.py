
def jdbc(ss, db_url, db_user, db_password, db_table):
    return ss.read.format("jdbc") \
        .option("url", db_url) \
        .option("encrypt", "false") \
        .option("sslValidateCertificate", "false") \
        .option("user", db_user) \
        .option("password", db_password) \
        .option("dbtable", db_table) \
        .load()
