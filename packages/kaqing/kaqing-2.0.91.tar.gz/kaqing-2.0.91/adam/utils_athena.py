import functools
import time
import boto3

from adam.config import Config
from adam.utils import lines_to_tabular, log, log2

@functools.lru_cache()
def audit_table_names():
   region_name = Config().get('audit.athena.region', 'us-west-2')
   database_name = Config().get('audit.athena.database', 'audit')
   catalog_name = Config().get('audit.athena.catalog', 'AwsDataCatalog')

   athena_client = boto3.client('athena', region_name=region_name)
   paginator = athena_client.get_paginator('list_table_metadata')

   table_names = []
   for page in paginator.paginate(CatalogName=catalog_name, DatabaseName=database_name):
      for table_metadata in page.get('TableMetadataList', []):
         table_names.append(table_metadata['Name'])

   return table_names

@functools.lru_cache()
def audit_column_names(tables: list[str] = [], database: str = None):
   if not database:
      database = Config().get('audit.athena.database', 'audit')

   if not tables:
      tables = Config().get('audit.athena.tables', 'audit').split(',')

   table_names = "'" + "','".join([table.strip() for table in tables]) + "'"

   query = f"select column_name from information_schema.columns where table_name in ({table_names}) and table_schema = '{database}'"
   _, _, rs = audit_query(query)
   if rs:
      return [row['Data'][0].get('VarCharValue') for row in rs[1:]]

   return []

def run_audit_query(sql: str, database: str = None):
   state, reason, rs = audit_query(sql, database)

   if state == 'SUCCEEDED':
      if rs:
         column_info = rs[0]['Data']
         columns = [col.get('VarCharValue') for col in column_info]
         lines = []
         for row in rs[1:]:
               row_data = [col.get('VarCharValue') for col in row['Data']]
               lines.append('\t'.join(row_data))

         log(lines_to_tabular(lines, header='\t'.join(columns), separator='\t'))
   else:
      log2(f"Query failed or was cancelled. State: {state}")
      log2(f"Reason: {reason}")

def audit_query(sql: str, database: str = None) -> tuple[str, str, list]:
   athena_client = boto3.client('athena')

   if not database:
      database = Config().get('audit.athena.database', 'audit')

   s3_output_location = Config().get('audit.athena.output', 's3://s3.ops--audit/ddl/results')

   response = athena_client.start_query_execution(
      QueryString=sql,
      QueryExecutionContext={
            'Database': database
      },
      ResultConfiguration={
            'OutputLocation': s3_output_location
      }
   )

   query_execution_id = response['QueryExecutionId']

   while True:
      query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
      state = query_status['QueryExecution']['Status']['State']
      if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
      time.sleep(1)

   if state == 'SUCCEEDED':
      results_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
      if results_response['ResultSet']['Rows']:
         return (state, None, results_response['ResultSet']['Rows'])

      return (state, None, [])
   else:
      return (state, query_status['QueryExecution']['Status'].get('StateChangeReason'), [])