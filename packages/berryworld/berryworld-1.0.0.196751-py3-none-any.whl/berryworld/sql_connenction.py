import os
import re
import ast
import math
import pyodbc
import traceback
import numpy as np
import pandas as pd
import sqlalchemy as sa
from urllib import parse
from numbers import Number


class SQLConnection:
    """ Connect to Microsoft SQL """

    def __init__(self, db_reference, server, master=False, trusted_certificate=True, encrypt=True, multi_db=False):
        """ Initialize the class
        It requires the
        SQL-DBREFERENCE-PROD = 'server_name db_name user password'
        -----------------------------
        db_reference = 'FruitFlow'
        server = 'prod'

        con_ = SQLConnection(db_reference, server)
        -----------------------------
        :param db_reference: Database reference to connect to
        :param server: Server to connect to
        :param master: Indicate whether the connection will be done to master or to a specific database
        :param trusted_certificate: Indicate whether the connection will be done using the TrustServerCertificate
        :param encrypt: Indicate whether the connection will use SSL/TLS encryption
        :param multi_db: Indicate whether the connection will be done to a specific database or to multiple databases
        """
        self.db_reference = db_reference.replace("_", "") if "_" in db_reference else db_reference
        self.server = server
        if self.server is None:
            raise ValueError("Please provide a value for server type")

        self.multi_db = multi_db
        self.master = master
        if trusted_certificate:
            self.trusted_certificate = '&TrustServerCertificate=yes'
        else:
            self.trusted_certificate = ''

        if encrypt:
            self.encrypt = '&Encrypt=yes'
        else:
            self.encrypt = ''

        drivers = [driver for driver in pyodbc.drivers() if (bool(re.search(r'\d', driver)))]
        try:
            self.server_name, self.db_name, self.user_name, self.password = self.credentials()
        except Exception as e:
            raise ValueError(f"Cannot find a reference to {self.db_reference} and {self.server.upper()} server: {str(e)}")

        self.con = None
        self.engine = None
        self.con_string = None

        driver_attempt = ''
        for driver in drivers:
            try:
                self.driver = driver
                self.query('''SELECT TOP 1 * FROM information_schema.tables;''')
                break
            except Exception as e:
                print(e)
                driver_attempt = str(e)

        if driver_attempt != '':
            raise ValueError(
                f"Cannot connect to db: {self.db_name} - Error: {str(driver_attempt)}")

    def credentials(self):
        """ Return the credentials used to connect to the SQL Server
        :return: Dictionary with the credentials used to connect to the SQL Server
        """
        try:
            server_creds = os.environ.get(f"SQL-{self.db_reference.upper()}")
            server_creds = ast.literal_eval(server_creds)
        except Exception as e:
            raise ValueError(f'DB reference: {self.db_reference} not found. ERROR: {e}')

        try:
            server_creds = server_creds[self.server.lower()]
        except Exception as e:
            raise ValueError(f'Server: {self.server} not found for DB reference: {self.db_reference}. ERROR: {e}')

        if 'server_name' not in server_creds.keys():
            raise ValueError(f"Server name not provided for {self.db_reference} on {self.server.upper()} server")
        else:
            server_name = server_creds['server_name']

        if 'db_name' not in server_creds.keys():
            raise ValueError(f"Database name not provided for {self.db_reference} on {self.server.upper()} server")
        else:
            db_name = server_creds['db_name']

        if 'user_name' not in server_creds.keys():
            raise ValueError(f"User name not provided for {self.db_reference} on {self.server.upper()} server")
        else:
            user_name = server_creds['user_name']

        if 'pwd' not in server_creds.keys():
            raise ValueError(f"Password not provided for {self.db_reference} on {self.server.upper()} server")
        else:
            password = server_creds['pwd']

        return re.sub(r'(\\)\1*', r'\1', server_name), db_name, user_name, password

    def open_read_connection(self, commit_as_transaction=True):
        """ Open a reading connection with the Server
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: The opened connection
        """
        if self.master:
            self.con_string = ('mssql+pyodbc://' + self.user_name + ':%s@' + self.server_name + '/master' +
                              '?driver=' + self.driver + '&trusted_connection=yes' + self.trusted_certificate +
                               self.encrypt)
            self.engine = sa.create_engine(self.con_string % parse.quote_plus(self.password))
        else:
            self.con_string = ('mssql+pyodbc://' + self.user_name + ':%s@' + self.server_name + '/' + self.db_name +
                              '?driver=' + self.driver + self.trusted_certificate + self.encrypt)
            self.engine = sa.create_engine(self.con_string % parse.quote_plus(self.password))
        if not commit_as_transaction:
            self.engine = self.engine.execution_options(isolation_level="AUTOCOMMIT")

        self.con = self.engine.connect().connection

    def open_write_connection(self, commit_as_transaction=True):
        """ Open a writing connection with the Server
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: The opened connection
        """
        database = self.db_name
        if self.multi_db & (self.server.lower() == 'prod'):
            database = str(self.db_name) + 'Primary'

        constring = ('mssql+pyodbc://' + self.user_name + ':%s@' + self.server_name + '/' + database +
                    '?driver=' + self.driver + self.trusted_certificate + self.encrypt)
        self.engine = sa.create_engine(constring % parse.quote_plus(self.password))
        if not commit_as_transaction:
            self.engine = self.engine.execution_options(isolation_level="AUTOCOMMIT")

        self.con = self.engine.connect().connection

    def close_connection(self):
        """ Close any opened connections with the Server
        :return: None
        """
        self.con.close()
        if self.engine:
            self.engine.dispose()

    @staticmethod
    def _chunker(seq, size):
        """ Split the data set in chunks to be sent to SQL
        :param seq: Sequence of records to be split
        :param size: Size of any of the chunks to split the data
        :return: The DataFrame divided in chunks
        """
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def query(self, sql_query, coerce_float=False):
        """ Read data from SQL according to the sql_query
        -----------------------------
        query_str = "SELECT * FROM %s" & table
        con_.query(query_str)
        -----------------------------
        :param sql_query: Query to be sent to SQL
        :param coerce_float: Attempt to convert values of non-string, non-numeric objects (like decimal.Decimal)
        to floating point.
        :return: DataFrame gathering the requested data
        """
        self.open_read_connection()
        data = None
        try:
            with self.engine.begin() as conn:
                data = pd.read_sql_query(sa.text(sql_query), conn, coerce_float=coerce_float)
        except ValueError:
            print(traceback.format_exc())
        finally:
            self.close_connection()
        return data

    @staticmethod
    def _parse_df(parse_, data, col_names):
        """ Auxiliar function to convert list to DataFrame
        :param parse_: Parameter to indicate whether the data has to be transformed into a DataFrame or not
        :param data: List gathering the data retrieved from SQL
        :param col_names: List of columns to create the DataFrame
        :return: Formatted data
        """
        if parse_ is True:
            col_names = list(zip(*list(col_names)))[0]
            res = pd.DataFrame(list(zip(*data)), index=col_names).T
        else:
            res = [col_names, data]
        return res

    def sp_results(self, sql_query, resp_number=None, parse_=True, commit_as_transaction=True, no_count=True):
        """ Execute a stored procedure and retrieves all its output data
        -----------------------------
        query_str = "EXECUTE %s" & stored_procedure
        con_.sp_results(query_str, resp_number=1)
        -----------------------------
        :param sql_query: Query to be sent to SQL
        :param resp_number: Indicate which of the stored procedures responses will be retrieved
        :param parse_: Indicate whether the output needs to be converted to a DataFrame or not
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :param no_count: Indicate whether SET NOCOUNT option is ON (True) or OFF (False)
        :return: DataFrame list gathering the requested data
        """
        self.open_write_connection(commit_as_transaction)
        data_list = list()
        cursor = None
        try:
            cursor = self.con.cursor()
            if no_count:
                cursor.execute("SET NOCOUNT ON;" + sql_query)
            else:
                cursor.execute(sql_query)
            if resp_number is not None:
                for cursor_number in range(resp_number - 1):
                    cursor.nextset()
                try:
                    data_list.append(self._parse_df(parse_, cursor.fetchall(), cursor.description))
                except ValueError:
                    raise ValueError('Please indicate a valid resp_number')
            else:
                aux_cursor = True
                count = 0
                while aux_cursor is not False and count < 100:
                    try:
                        data_list.append(self._parse_df(parse_, cursor.fetchall(), cursor.description))
                        aux_cursor = cursor.nextset()
                    except Exception as e:
                        print(e)
                        cursor.nextset()
                    finally:
                        count += 1
                    if count >= 100:
                        raise RuntimeError("Method sp_results has loop over 100 times for database '%s' on server '%s'"
                                           % (self.db_name, self.server))
            self.con.commit()
        except ValueError:
            print(traceback.format_exc())
        finally:
            if cursor:
                cursor.close()
            self.close_connection()
        return data_list

    def run_statement(self, sql_statement, commit_as_transaction=True):
        """ Execute SQL statement
        -----------------------------
        query_str = "DELETE FROM %s WHERE Id > 100" & table
        con_.run_statement(query_str)
        -----------------------------
        :param sql_statement: Statement as string to be run in SQL
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: Statement result
        """
        self.open_write_connection(commit_as_transaction)
        cursor = self.con.cursor()
        # Execute SQL statement
        try:
            cursor.execute(sql_statement)
            self.con.commit()
        except Exception:
            raise Exception(traceback.format_exc())
        finally:
            if cursor:
                cursor.close()
            self.close_connection()

    def insert(self, data, schema, table, truncate=False, delete=False, identity=False, chunk=1000, print_sql=False,
               commit_all_together=False, output=None, bools2bits=True, nullable=False, commit_as_transaction=True,
               infer_datetime_format=None):
        """ Insert data in a table in SQL truncating the table if needed
        -----------------------------
        df = pd.DataFrame({'col1': ['a', 'b'], 'col2': [1, 2]})
        con_.insert(df, table_schema, table_name)
        -----------------------------
        :param data: DataFrame containing the data to upload
        :param schema: Schema of the table in which the data will be uploaded
        :param table: Table in which the data will be uploaded
        :param truncate: Indicate whether the table has to be truncated before the data is sent or not
        :param delete: Delete the rows from a table (Suitable for tables that cannot be truncated because of
        external constraints)
        :param identity: Indicate whether the identity columns will be inserted or not
        :param chunk: Indicate how many rows will be uploaded at once
        :param print_sql: boolean to indicate that you want the sql_statement to be printed on the console
        :param commit_all_together: when it is true, it only commits data if all data has been inserted. When it is
                                    false, it commits data by chunks.
        :param output: Outputs the columns indicated in this list
        :param bools2bits: Indicate whether the Boolean columns should be converted to BIT to be inserted into SQL
        :return: A DataFrame with the output columns requested if output is not None, else None
        :param nullable: Used within bools2bits function to indicate which boolean column values to convert
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :param infer_datetime_format: Indicate whether the datetime columns should be converted to string and if so,
        then the format to be used
        """
        if output is None:
            output = []
        if data is None:
            # no data to upload
            return ValueError("The data provided is invalid!")
        cursor = None
        self.open_write_connection(commit_as_transaction)
        results = pd.DataFrame(columns=output)

        # Mapping the date datatype columns for SQL
        data = self.date_mapping_data_types(data)

        # Infer datetime format if provided
        if infer_datetime_format is not None:
            data = self.infer_datetime(data, infer_datetime_format)

        # Mapping the boolean columns to bit
        if bools2bits:
            data = self.boolean_mapping_data_types(data, nullable)

        try:
            cursor = self.con.cursor()
            # Truncate table if needed
            if truncate:
                cursor.execute("TRUNCATE TABLE [%s].[%s]" % (schema, table))
            # Delete all records from the table if needed
            if delete:
                cursor.execute("DELETE FROM [%s].[%s]" % (schema, table))
            # Allow to insert to an Identity column
            if identity:
                cursor.execute("SET IDENTITY_INSERT [%s].[%s] ON" % (schema, table))
            # Convert category columns to string
            cat_cols = data.columns[(data.dtypes == 'category').values].to_list()
            data[cat_cols] = data[cat_cols].astype(str)
            # Deal with bull values and apostrophes (')
            data = data.replace("'NULL'", "NULL")
            data = data.replace("'", "~~", regex=True).infer_objects(copy=False)
            data = data.fillna("null")
            # Insert data into the table destination
            records = [tuple(x) for x in data.values]
            insert_ = """INSERT INTO [%s].[%s] """ % (schema, table)
            insert_ += str(tuple(data.columns.values)).replace(
                "(\'", "([").replace('\', \'', '], [').replace('\')', '])')
            if len(output) > 0:
                insert_ += " OUTPUT Inserted.[" + "], Inserted.[".join(output) + "] "
            insert_ += """ VALUES """

            for batch in self._chunker(records, chunk):
                rows = str(batch).strip('[]').replace("~~", "''")
                rows = rows.replace("'NULL'", "NULL").replace("'null'", 'null')
                string = insert_ + rows
                string = self.convert_decimal_str(string)
                if print_sql:
                    print(string)
                cursor.execute(string)
                if len(output) > 0:
                    results = pd.concat([results, pd.DataFrame.from_records(cursor.fetchall(), columns=output)])
                if ~commit_all_together:
                    self.con.commit()
            if commit_all_together:
                self.con.commit()

            # Restrict to insert to an Identity column
            if identity:
                cursor.execute("SET IDENTITY_INSERT [%s].[%s] OFF" % (schema, table))

            if len(output) > 0:
                return results.reset_index(drop=True)

        except Exception:
            raise Exception(traceback.format_exc())

        finally:
            if cursor:
                cursor.close()
            self.close_connection()

    def insert_at_once(self, data, schema, table, truncate=False, delete=False, identity=False, chunk=1,
                       print_sql=False, output=None, bools2bits=True, nullable=False, commit_as_transaction=True):
        """ Build all the insert statements and commit them all at once
        -----------------------------
        df = pd.DataFrame({'col1': ['a', 'b'], 'col2': [1, 2]})
        con_.insert(df, table_schema, table_name)
        -----------------------------
        :param data: DataFrame containing the data to upload
        :param schema: Schema of the table in which the data will be uploaded
        :param table: Table in which the data will be uploaded
        :param truncate: Indicate whether the table has to be truncated before the data is sent or not
        :param delete: Delete the rows from a table (Suitable for tables that cannot be truncated because of
        external constraints)
        :param identity: Indicate whether the identity columns will be inserted or not
        :param chunk: Indicate how many rows will be uploaded at once
        :param print_sql: boolean to indicate that you want the sql_statement to be printed on the console
        :param output: Outputs the columns indicated in this list
        :param bools2bits: Indicate whether the Boolean columns should be converted to BIT to be inserted into SQL
        :param nullable: Used within bools2bits function to indicate which boolean column values to convert
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: A DataFrame with the output columns requested if output is not None, else None
        """
        if output is None:
            output = []
        if data is None:
            # no data to upload
            return ValueError("The data provided is invalid!")
        cursor = None
        self.open_write_connection(commit_as_transaction)
        results = pd.DataFrame(columns=output)

        # Mapping the date datatype columns for SQL
        data = self.date_mapping_data_types(data)

        # Mapping the boolean columns to bit
        if bools2bits:
            data = self.boolean_mapping_data_types(data, nullable)

        try:
            cursor = self.con.cursor()
            # Truncate table if needed
            if truncate:
                cursor.execute("TRUNCATE TABLE [%s].[%s]" % (schema, table))
            # Delete all records from the table if needed
            if delete:
                cursor.execute("DELETE FROM [%s].[%s]" % (schema, table))
            # Allow to insert to an Identity column
            if identity:
                cursor.execute("SET IDENTITY_INSERT [%s].[%s] ON" % (schema, table))
            # Convert category columns to string
            cat_cols = data.columns[(data.dtypes == 'category').values].to_list()
            data[cat_cols] = data[cat_cols].astype(str)
            # Deal with bull values and apostrophes (')
            data = data.replace("'NULL'", "NULL")
            data = data.replace("'", "~~", regex=True).infer_objects(copy=False)
            data = data.fillna("null")
            # Insert data into the table destination
            records = [tuple(x) for x in data.values]
            insert_ = """INSERT INTO [%s].[%s] """ % (schema, table)
            insert_ += str(tuple(data.columns.values)).replace(
                "(\'", "([").replace('\', \'', '], [').replace('\')', '])')
            if len(output) > 0:
                insert_ += " OUTPUT Inserted.[" + "], Inserted.[".join(output) + "] "
            insert_ += """ VALUES """

            insert_statements = list()
            for batch in self._chunker(records, chunk):
                rows = str(batch).strip('[]').replace("~~", "''")
                rows = rows.replace("'NULL'", "NULL").replace("'null'", 'null')
                string = insert_ + rows
                string = self.convert_decimal_str(string)
                insert_statements.append(string)

            if print_sql:
                print(';'.join(insert_statements))
            cursor.execute(';'.join(insert_statements))
            if len(output) > 0:
                results = pd.concat([results, pd.DataFrame.from_records(cursor.fetchall(), columns=output)])
            self.con.commit()

            # Restrict to insert to an Identity column
            if identity:
                cursor.execute("SET IDENTITY_INSERT [%s].[%s] OFF" % (schema, table))

            if len(output) > 0:
                return results.reset_index(drop=True)

        except Exception:
            raise Exception(traceback.format_exc())

        finally:
            if cursor:
                cursor.close()
            self.close_connection()

    def update(self, data, update_list, on_list, schema, table, bool_cols=None, print_sql=False, batch_size=100,
               output=None, nullable=True, commit_as_transaction=True):
        """ This method updates a table in batches in sql server.
        -----------------------------
        UPDATE [SCHEMA].[TABLE]
        SET update_list[0] = data[index, update_list{0}],
            update_list[1] = data[index, update_list[1]]
        OUTPUT output[0], output[1]
        WHERE on_list[0] = data[index, on_list[0]]
                AND on_list[1] = data[index, on_list[1]]
        -----------------------------
        :param data: DataFrame containing the data to update
        :param update_list: list of columns to update
        :param on_list: list of columns to apply the on clause
        :param schema: Schema of the table in which the data will be uploaded
        :param table: Table in which the data will be uploaded
        :param bool_cols: list of columns gathering boolean types
        :param print_sql: boolean to indicate that you want the sql_statement to be printed on the console
        :param bool_cols: columns to include as booleans
        :param batch_size: Number of records to update in each iteration
        :param output: Outputs the columns indicated in this list as a DataFrame. It should indicate if the column to
        retrieve is the inserted one or the deleted one (If nothing is indicated, then the Deleted one will be
        retrieved)
        :param nullable: Indicate whether to update the table column with null or exclude the reference from the update
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: None
        """
        cursor = None
        if data is None:
            # no data to update
            return ValueError("The data provided is invalid!")

        if output is None:
            output = []
        else:
            output = [out if 'inserted' in out.lower() or 'deleted' in out.lower() else 'Deleted.[' + out + ']' for out
                      in output]
        results = pd.DataFrame(columns=output)

        # re-starting indexes
        data.reset_index(drop=True, inplace=True)

        # Mapping boolean columns
        if bool_cols is not None:
            for col in bool_cols:
                data[col] = data[col].astype(bool)

        # Mapping date type for SQL
        data = self.date_mapping_data_types(data)

        # create connection
        self.open_write_connection(commit_as_transaction)

        try:
            # initialise cursor
            cursor = self.con.cursor()

            # extraction of the useful columns
            data_update = data[list(set(update_list + on_list))]

            # initialisation of the sql statement
            sql_start = ''' UPDATE [%s].[%s] SET ''' % (schema, table)
            iter_batch = math.ceil(data_update.shape[0] / batch_size)
            for batch in range(iter_batch):
                batch_update = data_update.iloc[batch * batch_size: (batch + 1) * batch_size]

                sql_statement = ''
                for iindex in batch_update.index:
                    # UPDATE [SCHEMA].[TABLE]
                    sql_statement += sql_start

                    # VALUES
                    for col in update_list:
                        if nullable:
                            if pd.isna(batch_update.loc[iindex, col]):
                                sql_statement += " [%s] = NULL ," % col
                            elif isinstance(batch_update.loc[iindex, col], bool):
                                sql_statement += " [%s] = %s ," % (col, int(batch_update.loc[iindex, col]))
                            elif isinstance(batch_update.loc[iindex, col], Number):
                                sql_statement += " [%s] = %s ," % (col, batch_update.loc[iindex, col])
                            else:
                                sql_statement += " [%s] = '%s' ," % (col, batch_update.loc[iindex, col])
                        else:
                            if pd.notna(batch_update.loc[iindex, col]):
                                if str(batch_update.loc[iindex, col]).upper() == 'NULL':
                                    continue
                                elif isinstance(batch_update.loc[iindex, col], bool):
                                    sql_statement += " [%s] = %s ," % (col, int(batch_update.loc[iindex, col]))
                                elif isinstance(batch_update.loc[iindex, col], Number):
                                    sql_statement += " [%s] = %s ," % (col, batch_update.loc[iindex, col])
                                else:
                                    sql_statement += " [%s] = '%s' ," % (col, batch_update.loc[iindex, col])

                    # OUTPUT
                    if len(output) > 0:
                        sql_statement = sql_statement[:-1] + " OUTPUT " + ",".join(output) + ' '

                    # WHERE
                    sql_statement = sql_statement[:-1] + ' WHERE '
                    for col in on_list:
                        if pd.isna(batch_update.loc[iindex, col]):
                            sql_statement += " [%s] = NULL AND" % col
                        elif isinstance(batch_update.loc[iindex, col], bool):
                            sql_statement += " [%s] = %s ," % (col, int(batch_update.loc[iindex, col]))
                        elif isinstance(batch_update.loc[iindex, col], Number):
                            sql_statement += " [%s] = %s AND" % (col, batch_update.loc[iindex, col])
                        else:
                            sql_statement += " [%s] = '%s' AND" % (col, batch_update.loc[iindex, col])

                    # Addition of semicolon
                    sql_statement = sql_statement[:-3] + ';'

                if print_sql:
                    print(sql_statement)

                # executing statement
                if len(sql_statement) > 0:
                    if len(output) > 0:
                        cursor.execute(sql_statement)
                        for cursor_number in range(len(sql_statement.split(';')) - 1):
                            results = pd.concat([results, pd.DataFrame.from_records(cursor.fetchall(), columns=output)])
                            cursor.nextset()
                    else:
                        cursor.execute(sql_statement)
                    self.con.commit()

            if len(output) > 0:
                return results.reset_index(drop=True)

        except Exception:
            raise Exception(traceback.format_exc())

        finally:
            if cursor:
                cursor.close()
            self.close_connection()

    def bulk_update(self, data, update_list, on_list, schema, table, bool_cols=None, print_sql=False, output=None,
                    chunk=1000, commit_as_transaction=True):
        """ This method updates a table in batches in sql server.
        -----------------------------
        UPDATE [SCHEMA].[TABLE]
        SET update_list[0] = data[index, update_list{0}],
            update_list[1] = data[index, update_list[1]]
        OUTPUT output[0], output[1]
        WHERE on_list[0] = data[index, on_list[0]]
                AND on_list[1] = data[index, on_list[1]]
        -----------------------------
        :param data: DataFrame containing the data to update
        :param update_list: list of columns to update
        :param on_list: list of columns to apply the on clause
        :param schema: Schema of the table in which the data will be uploaded
        :param table: Table in which the data will be uploaded
        :param bool_cols: list of columns gathering boolean types
        :param print_sql: boolean to indicate that you want the sql_statement to be printed on the console
        :param bool_cols: columns to include as booleans
        :param output: Outputs the columns indicated in this list as a DataFrame. It should indicate if the column to
        retrieve is the inserted one or the deleted one (If nothing is indicated, then the Deleted one will be
        retrieved)
        :param chunk: Indicate how many rows will be uploaded at once
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: None
        """
        cursor = None
        if data is None:
            # no data to update
            return ValueError("The data provided is invalid!")

        if output is None:
            output = []
            sql_output = []
        else:
            sql_output = [out if 'inserted' in out.lower() or 'deleted' in out.lower() else 'Deleted.[' + out + ']' for
                          out
                          in output]
        results = pd.DataFrame(columns=output)

        # re-starting indexes
        data.reset_index(drop=True, inplace=True)

        # Mapping boolean columns
        if bool_cols is not None:
            for col in bool_cols:
                data[col] = data[col].astype(bool)

        # Mapping date type for SQL
        data = data[on_list + update_list]
        data = self.date_mapping_data_types(data)

        # create connection
        self.open_write_connection(commit_as_transaction)

        try:
            # initialise cursor
            cursor = self.con.cursor()

            # Convert category columns to string
            cat_cols = data.columns[(data.dtypes == 'category').values].to_list()
            data[cat_cols] = data[cat_cols].astype(str)
            # Deal with bull values and apostrophes (')
            data = data.replace("'NULL'", "NULL")
            data = data.replace("'", "~~", regex=True).infer_objects(copy=False)
            data = data.fillna("null")

            records = [tuple(x) for x in data.values]
            temp_table = f'#Temp{schema}{table}'

            for batch in self._chunker(records, chunk):
                batch_records = [tuple(x) for x in batch]
                # initialisation of the sql statement
                insert_ = f'DROP TABLE IF EXISTS {temp_table} '
                insert_ += f"SELECT * INTO {temp_table} FROM ( VALUES  "
                temp_columns = str(tuple(data.columns.values)).replace("(\'", "([").replace(
                    '\', \'', '], [').replace('\')', '])')
                rows = str(batch_records).strip('[]').replace("~~", "''")
                rows = rows.replace("'NULL'", "NULL").replace("'null'", 'null')
                sql_statement = insert_ + rows
                sql_statement = self.convert_decimal_str(sql_statement)
                sql_statement += f') AS TempTable {temp_columns}'

                col_update_set = ''
                for col in update_list:
                    col_update_set += f' target.{col} = source.{col},'
                col_update_set = col_update_set[:-1]

                col_difference_check = ''
                for col in update_list:
                    col_difference_check += f' target.{col} <> source.{col} OR'
                col_difference_check = col_difference_check[:-2]

                col_join_on = ''
                for col in on_list:
                    col_join_on += f' source.{col} = target.{col} AND'
                    col_join_on = col_join_on[:-3]

                sql_statement += f'UPDATE target SET {col_update_set} '

                if len(output) > 0:
                    sql_statement += f" OUTPUT {','.join(sql_output)} "

                sql_statement += f'''FROM {schema}.{table} target
                                        JOIN {temp_table} as source
                                            ON {col_join_on}
                                     WHERE {col_difference_check}
                                '''

                sql_statement += f' DROP TABLE IF EXISTS {temp_table} '

                if print_sql:
                    print(sql_statement)

                # executing statement
                if len(sql_statement) > 0:
                    if len(output) > 0:
                        cursor.execute(sql_statement)
                        cursor.nextset()
                        results = pd.concat([results, pd.DataFrame.from_records(cursor.fetchall(), columns=output)])
                    else:
                        cursor.execute(sql_statement)

                self.con.commit()

            if len(output) > 0:
                return results.reset_index(drop=True)

        except Exception:
            raise Exception(traceback.format_exc())

        finally:
            if cursor:
                cursor.close()
            self.close_connection()

    def merge(self, data, staging_schema, staging_table, sp_schema, sp_name, truncate=False, chunk=1000,
              commit_as_transaction=True):
        """ Merge data from Staging table using a Stored Procedure. It requires a table in SQL which will store the
        Staging data. The method will work as follows:
        1.- Truncate the staging table according to the truncate parameter
        2.- Insert the data into the staging table
        3.- Execute a stored procedure to merge the staging table with the destination table
        -----------------------------
        df = pd.DataFrame({'col1': ['a', 'b'], 'col2': [1, 2]})
        con_.merge(df, staging_schema, staging_table, sp_schema, sp_name, truncate=True)
        -----------------------------
        :param data: DataFrame to insert in the staging table
        :param staging_schema: Staging table schema
        :param staging_table: Staging table name
        :param sp_schema: Stored Procedure schema
        :param sp_name: Stored Procedure name
        :param truncate: Indicate whether the staging table has to be truncated or not
        :param chunk: Indicate how many rows will be uploaded at once
        :param commit_as_transaction: Indicate whether the connection will be done using the autocommit option or not
        :return: None
        """
        if data is None:
            # no data to upload
            return ValueError("The data provided is invalid!")
        cursor = None
        self.open_write_connection(commit_as_transaction)
        try:
            cursor = self.con.cursor()
            # Truncate Staging table if needed
            if truncate:
                trunc_insert = """TRUNCATE TABLE [%s].[%s]""" % (staging_schema, staging_table)
                cursor.execute(trunc_insert)
                self.con.commit()
            # Convert category columns to string
            cat_cols = data.columns[(data.dtypes == 'category').values].to_list()
            data[cat_cols] = data[cat_cols].astype(str)
            # Deal with null values and apostrophes (')
            data = data.replace("'NULL'", "NULL")
            data = data.replace("'", "~~", regex=True).infer_objects(copy=False)
            data = data.fillna("null")
            # Insert in Staging Table
            records = [tuple(x) for x in data.values]
            insert_ = """INSERT INTO [%s].[%s] """ % (staging_schema, staging_table)
            insert_ = insert_ + str(tuple(data.columns.values)).replace("\'", "") + """ VALUES """
            for batch in self._chunker(records, chunk):
                rows = str(batch).strip('[]').replace("~~", "''")
                rows = rows.replace("'NULL'", "NULL").replace("'null'", 'null')
                string = insert_ + rows
                string = self.convert_decimal_str(string)
                cursor.execute(string)
                self.con.commit()
            # Execute Stored Procedure
            exec_sp = """EXECUTE [%s].[%s]""" % (sp_schema, sp_name)
            cursor.execute(exec_sp)
            self.con.commit()
        except Exception:
            raise Exception(traceback.format_exc())
        finally:
            if cursor:
                cursor.close()
            self.close_connection()

    def merge_into(self, data, schema, table, on_list, update_check=False, update_set=None, bool_cols=None,
                   identity=False, print_sql=False, nullable=False):
        """
        This method is equivalent to the 'merge into' of T-sql. Schema and table defines the Target, while data is the
        Source. Please refer to below schema for more arguments use clarifications.
        Aspects to take into consideration:
        1.- This method will not work properly if data contains duplicates. It is not relevant if the target contains
            duplicates because DISTINCT is used to call the table.
        2.- When having booleans in the dataset you have to pay attention because pandas get bool from sql server as
            [True, False], instead of [0,1]. The method need data from type boolean to be inserted as [0, 1].
        3.- When dealing with datetime columns a similar problem arises. time_format is a dict that contains as keys
            the name of a date column and as values the format that the columns has to have.
        Versions comments...
        + Difference between version 1.0 and 1.01 is that the last one is a bit simpler, it waits for names of columns
          which types are booleans or datetime (and format for this one) instead of trying to figure out this columns
          as in version 1.0 what is sometimes problematic. So, version 1.01 is more reliable but requires more time
          to write the call to the method.
        -------------------------
        MERGE INTO [SCHEMA].[TABLE] AS TARGET
        USING (
                data
                ) AS SOURCE
                ON TARGET.on_list[0] = SOURCE.on_list[0]
                   AND TARGET.on_list[1] = SOURCE.on_list[1]
                   ...
                   AND TARGET.on_list[n] = SOURCE.on_list[n]
        WHEN MATCHED AND (
                    TARGET.update_check[0] <> SOURCE.update_check[0]
                    OR TARGET.update_check[1] <> SOURCE.update_check[1]
                    ...
                    OR TARGET.update_check[n] <> SOURCE.update_check[n]
                    )
            UPDATE SET  TARGET.update_check[0] = SOURCE.update_check[0],
                        ...
                        TARGET.update_check[n] = SOURCE.update_check[n],
                        TARGET.update_set[0] = SOURCE.update_set[0],
                        TARGET.update_set[1] = SOURCE.update_set[1],
                        ....
                        TARGET.update_set[n] = SOURCE.update_set[n]
        WHEN NOT MATCHED BY TARGET THEN
            INSERT
            (
            all columns from [SCHEMA].[TABLE]
            )
            VALUES
            (all columns from data)
         -------------------------------
        :param data: DataFrame containing the data to upload/update
        :param schema: Schema of the table in which the data will be uploaded
        :param table: Table in which the data will be uploaded
        :param on_list: list of columns to apply the on clause
        :param update_check: list of columns to do the check
        :param update_set: list of columns to update
        :param bool_cols: list of columns gathering boolean types
        :param identity: Indicate whether the identity columns will be inserted or not, only make sense when the table
        in its definition has it. Its a boolean.
        :param print_sql: boolean to indicate that you want the sql_statement to be printed on the console
        :return: None
        :param nullable: Used for the boolean_mapping_data_types to indicate which boolean column values to convert
        """
        if data is None:
            # no data to upload
            return ValueError("The data provided is invalid!")

        if data.shape[0] != data.drop_duplicates().shape[0]:
            return TypeError("There are duplicates values in your dataframe, it will not work properly on "
                             "pd.concat().drop_duplicates()")

        # if update_set has values assigned, update check has to have values assigned
        if update_set is not None:
            if update_check is None:
                return ValueError("Please, to use update_set assigned values to update_check")
        else:
            update_set = update_check

        # Mapping boolean columns
        if bool_cols is not None:
            for col in bool_cols:
                data[col] = data[col].astype(bool)

        # Mapping date and boolean type for SQL
        data = self.date_mapping_data_types(data)
        data = self.boolean_mapping_data_types(data, nullable)

        try:
            # call the table from the server
            data_table = self.query("""SELECT DISTINCT * FROM [%s].[%s]""" % (schema, table))

            if data_table.shape[0] == 0:
                print("The destination table is empty so all the data will be inserted")
                self.insert(data, schema, table)

            else:
                for data_col in data.columns:
                    if ("int" in str(type(data_table[data_col].iloc[0]))) & (
                            data_table[data_col].isnull().sum() > 0):
                        data_table[data_col] = data_table[data_col].astype(float)
                    else:
                        data_table[data_col] = data_table[data_col].astype(type(data[data_col].iloc[0]))

                coincidence = pd.DataFrame()
                if data_table.shape[0] > 0:
                    for col in data_table.columns.values.tolist():
                        if isinstance(data_table.loc[0, col], bool):
                            data_table[col] = data_table[col].apply(
                                lambda x: 1 if x is True else 0 if x is False else np.NaN)
                    if bool_cols is not None:
                        for col in bool_cols:
                            data_table[col] = data_table[col].astype(bool)
                    # join the input table with the one in the database
                    coincidence = data.merge(data_table[on_list], how='inner', on=on_list)
                    # WHEN MATCHED AND ... UPDATE SET
                    if update_check:
                        coincidence2 = coincidence.merge(data_table[list(set(on_list + update_check))],
                                                         how='inner',
                                                         on=list(set(on_list + update_check)))
                        data_update = pd.concat([coincidence, coincidence2], ignore_index=True)
                        data_update.drop_duplicates(keep=False, inplace=True)
                        if data_update.shape[0] > 0:
                            self.update(data_update, list(set(update_set + update_check)), on_list, schema, table,
                                        print_sql=print_sql)

                # WHEN NOT MATCHED BY TARGET THEN... INSERT
                data_insert = pd.concat([data, coincidence], ignore_index=True)
                data_insert.drop_duplicates(keep=False, inplace=True)
                if data_insert.shape[0] > 0:
                    self.insert(data_insert, schema, table, identity=identity, print_sql=print_sql)

        except Exception:
            raise Exception(traceback.format_exc())

    @staticmethod
    def date_mapping_data_types(data):
        """
        Map datetime and boolean variables so they can be inserted in SQL
        :param data: DataFrame containing the variables to map
        :return: The mapped DataFrame
        """
        first_index = data.index[0]
        date_col = data.columns[
            [('date' in str(type(data.loc[first_index, col]))) | ('timestamp' in str(type(data.loc[first_index, col])))
             for col in data.columns]]
        if len(date_col) > 0:
            for col in date_col:
                data[col] = pd.to_datetime(data[col])
                if data[col].dtypes == 'O':
                    data[col] = data[col].dt.strftime('%Y-%m-%d')
                else:
                    data[col] = data[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                data.loc[data[col] == 'NaT', col] = np.nan

        return data

    @staticmethod
    def boolean_mapping_data_types(data, nullable=False):
        """
        Map datetime and boolean variables so they can be inserted in SQL
        :param data: DataFrame containing the variables to map
        :return: The mapped DataFrame
        :param nullable: Determine if you want to convert null values within boolean columns to boolean format or not
        """
        first_index = data.index[0]
        bool_col = data.columns[
            [('bool' in str(type(data.loc[first_index, col]))) | ('object' in str(type(data.loc[first_index, col]))) for
             col in data.columns]]
        if len(bool_col) > 0:
            for col in bool_col:
                if nullable:
                    bool_not_null = data[data[col].notna()]
                    if bool_not_null.shape[0] > 0:
                        for iindex in bool_not_null.index:
                            data.at[iindex, col] = int(data.loc[iindex, col])
                else:
                    data[col] = data[col].apply(lambda x: 1 if x is True else 0)

        return data

    @staticmethod
    def id_next(con_db, table, schema, id_col, print_sql=False):
        """
        This static method returns the next id to be inserted into a table for sql_server
        :param con_db: class to connect to a sql server dabatase
        :param table: name of the table
        :param schema: name of the schema
        :param id_col: name of the id column
        :param print_sql: bool to indicate if you want sql statement to be print on Python Console
        :return: Max ID + 1 for id_col
        """
        sql_statement = ("SELECT CASE WHEN MAX(%s) IS NULL THEN 1 ELSE MAX(%s) + 1 END AS [Id] FROM [%s].[%s]" % (
            id_col, id_col, schema, table))
        if print_sql:
            print(sql_statement)
        df = con_db.query(sql_statement)
        id_ = df.loc[0, 'Id']
        return id_

    @staticmethod
    def convert_decimal_str(string):
        """ Method to parse the Decimal type in python
        :param string: String variable to parse
        """
        string = re.sub("'\)(?!(,[ ]+\())(?=([^$]))", "", string)
        return re.sub("Decimal\('", "", string)

    @staticmethod
    def infer_datetime(data, infer_datetime_format):
        """ Method to infer datetime columns and format them as string
        :param data: DataFrame to parse
        :param infer_datetime_format: format to be used for the datetime columns
        """
        for col in data.select_dtypes(include=['datetime64']).columns:
            data[col] = pd.to_datetime(data[col]).dt.strftime(infer_datetime_format)

        return data
