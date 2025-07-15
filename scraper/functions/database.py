import psycopg
from sqlalchemy import create_engine

class Database:
    def __init__(self, host="db", port=5432, dbname="vacancyScraperDb", user="postgres", password="password"):
        self.connection = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        self.cursor = self.connection.cursor()
        self.engine = create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}")


    def insert_data(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def write_df(self, df, table_name, if_exists="append", index=False):
        df.to_sql(name=table_name, con=self.engine, if_exists=if_exists, index=index)
        print(f"Written dataframe to {table_name}")

    def close(self):
        self.cursor.close()
        self.connection.close()

