import base64
import re
import inspect
from typing import Union, List, Optional, Literal
import pandas as pd
import requests
import os
from brynq_sdk_brynq import BrynQ
from brynq_sdk_functions import Functions
from .bank import Bank
from .company import Company
from .documents import CustomDocuments
from .employment import Employment
from .named_lists import NamedLists
from .payments import Payments
from .people import People
from .salaries import Salaries
from .timeoff import TimeOff
from .work import Work
from .custom_tables import CustomTables
from .payroll_history import History

class Bob(BrynQ):
    def __init__(self, system_type: Optional[Literal['source', 'target']] = None, test_environment: bool = True, debug: bool = False, target_system: str = None):
        super().__init__()
        self.timeout = 3600
        self.headers = self._get_request_headers(system_type)
        if test_environment:
            self.base_url = "https://api.sandbox.hibob.com/v1/"
        else:
            self.base_url = "https://api.hibob.com/v1/"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.people = People(self)
        self.salaries = Salaries(self)
        self.work = Work(self)
        self.bank = Bank(self)
        self.employment = Employment(self)
        self.payments = Payments(self)
        self.time_off = TimeOff(self)
        self.documents = CustomDocuments(self)
        self.companies = Company(self)
        self.named_lists = NamedLists(self)
        self.custom_tables = CustomTables(self)
        self.payroll_history = History(self)
        self.data_interface_id = os.getenv("DATA_INTERFACE_ID")
        self.debug = debug
        self.bob_dir = "bob_data"  # Directory to save Bob data files
        self.setup_schema_endpoint_mapping()

    def _get_request_headers(self, system_type):
        credentials = self.interfaces.credentials.get(system='bob', system_type=system_type)
        auth_token = base64.b64encode(f"{credentials.get('data').get('User ID')}:{credentials.get('data').get('API Token')}".encode()).decode('utf-8')
        headers = {
            "accept": "application/json",
            "Authorization": f"Basic {auth_token}",
            "Partner-Token": "001Vg00000A6FY6IAN"
        }

        return headers

    def get_paginated_result(self, request: requests.Request) -> List:
        has_next_page = True
        result_data = []
        while has_next_page:
            prepped = request.prepare()
            prepped.headers.update(self.session.headers)
            resp = self.session.send(prepped, timeout=self.timeout)
            resp.raise_for_status()
            response_data = resp.json()
            result_data += response_data['results']
            next_cursor = response_data.get('response_metadata').get('next_cursor')
            # If there is no next page, set has_next_page to False, we could use the falsy value of None but this is more readable
            has_next_page = next_cursor is not None
            if has_next_page:
                request.params.update({"cursor": next_cursor})

        return result_data

    #methods to be used in conjunction with teh scenario sdk. scenario sdks collects all schemas and correpodnign fields and passes it to the get_data_per_schema method, which needs this method to map the schema name to the corresponding endpoint.
    def setup_schema_endpoint_mapping(self):
        self.schema_endpoint_map = {
            "PeopleSchema": self.people,
            "SalarySchema": self.salaries,
            "WorkSchema": self.work,
            "BankSchema": self.bank,
            "EmploymentSchema": self.employment,
            "VariablePaymentSchema": self.payments,
            "ActualPaymentsSchema": self.payments,
            "TimeOffSchema": self.time_off,
            "TimeOffBalanceSchema": self.time_off,
            "PayrollHistorySchema": self.payroll_history,
            "CustomTableSchema": self.custom_tables,
            "CustomTableMetadataSchema": self.custom_tables,
            "NamedListSchema": self.named_lists,
            # Note: DocumentsSchema and CompanySchema don't have corresponding schema classes yet
            # but keeping them for backward compatibility
            "DocumentsSchema": self.documents,
            "CompanySchema": self.companies,
        }

    def get_data_for_schemas(self, schemas: dict[str, set], save_dir = None) -> dict:
        """
        Get data for each schema using the schema-to-fields mapping from the scenario SDK.

        This method integrates with the BrynQ scenario SDK to retrieve data based on schema
        definitions. It automatically maps schema names to the appropriate Bob API endpoints
        and retrieves only the fields specified in the schema-to-fields mapping.

        NOTE:
        "endpoint_obj" is just a variable that represents the specific Bob API client (or "endpoint") for a given type of data.
        For example, if you want to get people data, endpoint_obj would be self.people.
        If you want salary data, endpoint_obj would be self.salaries, and so on.
        Each of these endpoint objects knows how to fetch data for its specific schema/table from Bob.
        So, "endpoint_obj" is basically a shortcut to the right part of the Bob SDK that knows how to get the data you want.

        Args:
            schemas: Dictionary mapping schema names to sets of fields
                    Example: {'PeopleSchema': {'firstName', 'lastName', 'email'},
                             'WorkSchema': {'title', 'department', 'site'}}
            save_dir: Optional directory path to save parquet files. Can be a string or path object
                     (e.g., os.path.join(self.basedir, "data", "bob_to_zenegy")). If None, files are not saved to disk.

        Returns:
            Dictionary with results for each schema containing:
            - 'dataframe': The retrieved data as pandas DataFrame
            - 'filepath': Path where the data was saved as parquet file (None if save_dir is None)
            - 'fields': List of fields that were requested
            - 'status_message': Status message about field retrieval
            - 'status_level': Status level (INFO/WARNING/ERROR)

        Integration with Scenario SDK:
            This method is designed to work seamlessly with the BrynQ scenario SDK:
            1. Use scenarios.get_schema_field_mapping() to get schema-to-fields mapping
            2. Pass the mapping to this method to retrieve data
            3. The method automatically handles endpoint mapping and field selection
            4. Field tracking shows exactly which requested fields were returned vs missing

        Example usage:
            # Initialize Bob SDK
            bob = Bob(system_type='source')

            # Get schema-to-fields mapping from scenarios
            schema_fields = bob.interfaces.scenarios.get_schema_field_mapping()

            # Get data for specific schemas
            results = bob.get_data_for_schemas({
                'PeopleSchema': schema_fields['PeopleSchema'],
                'WorkSchema': schema_fields['WorkSchema']
            }, save_dir=os.path.join('data', 'bob_to_zenegy'))

            # Access results and status messages
            for schema_name, result in results.items():
                print(f"Schema: {schema_name}")
                print(f"Status: {result['status_message']}")
                print(f"Level: {result['status_level']}")
                print(f"Data shape: {result['dataframe'].shape}")
                print(f"Saved to: {result['filepath']}")

            # Process the data
            people_data = results['PeopleSchema']['dataframe']
            work_data = results['WorkSchema']['dataframe']

            # Example with path object
            custom_path = os.path.join('data', 'bob_to_zenegy')
            results_with_path = bob.get_data_for_schemas({
                'PeopleSchema': schema_fields['PeopleSchema']
            }, save_dir=custom_path)
        """
        results = {}

        # Validate input
        if not schemas:
            print("Warning: No schemas provided")
            return results

        # Process each schema
        for schema_name, fields in schemas.items():
            # Validate schema name and fields
            if not schema_name:
                print("Warning: Empty schema name provided, skipping")
                continue

            if not fields:
                print(f"Warning: No fields provided for schema '{schema_name}', skipping")
                continue

            # Get the endpoint/service for this schema
            endpoint_obj = self.schema_endpoint_map.get(schema_name)

            if endpoint_obj is None:
                print(f"Warning: No endpoint found for schema '{schema_name}'. Available schemas: {list(self.schema_endpoint_map.keys())}")
                continue

            try:
                # Get data using the service endpoint
                df_bob, status_message, status_level = self._handle_endpoint(endpoint_obj, list(fields), schema_name)
            except Exception as e:
                print(f"Error processing schema '{schema_name}': {str(e)}")
                results[schema_name] = {
                    'dataframe': pd.DataFrame(),
                    'filepath': None,
                    'fields': list(fields),
                    'status_message': f"Error processing schema '{schema_name}': {str(e)}",
                    'status_level': 'ERROR'
                }
                continue

            # Save the result
            if save_dir:
                filename = f"bob_{schema_name.replace(' ', '_')}.parquet"
                output_dir = save_dir if save_dir is not None else self.bob_dir
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, filename)
                df_bob.to_parquet(filepath)
            else:
                filepath = None

            results[schema_name] = {
                'dataframe': df_bob,
                'filepath': filepath,
                'fields': list(fields),
                'status_message': status_message,
                'status_level': status_level
            }
        return results

    def _handle_endpoint(self, endpoint_obj, body_fields: List[str], schema_name: str) -> tuple[pd.DataFrame, str, str]:
        """
        Handle data retrieval for a given endpoint object (e.g., self.people, self.work, etc.).

        Args:
            endpoint_obj: The endpoint object responsible for fetching data for a specific schema.
                For example, this could be self.people, self.work, self.salaries, etc.
                (Think of these as "API clients" or "data access classes" for each schema/table.)
            body_fields: List of fields to retrieve
            schema_name: Name of the schema being processed

        Returns:
            tuple[pd.DataFrame, str, str]: Dataframe, status message, and status level
        """
        get_method = endpoint_obj.get

        # Check if the method accepts field_selection parameter
        sig = inspect.signature(get_method)
        if 'field_selection' in sig.parameters and 'person_ids' not in sig.parameters:
            bob_data_valid, _ = get_method(field_selection=body_fields)
        # elif 'person_id' in sig.parameters:
        #     bob_data_valid, _ = self._fetch_data_with_person_id(get_method)
        # elif 'person_ids' in sig.parameters and 'field_selection' in sig.parameters:
        #     bob_data_valid, _ = self._fetch_data_with_person_ids(get_method, body_fields)
        else:
            bob_data_valid, _ = get_method()
        df_bob = pd.DataFrame(bob_data_valid)

        # Track field retrieval success/failure and handle missing fields
        status_message, status_level = self._log_field_retrieval_status(df_bob, body_fields, schema_name)

        return df_bob, status_message, status_level

    def _log_field_retrieval_status(self, df_bob: pd.DataFrame, body_fields: List[str], schema_name: str) -> tuple[str, str]:
        """
        Checks if the data returned from the Bob API actually contains all the fields you asked for.

        This function counts how many fields you requested (body_fields)
        and how many columns you actually got back in the DataFrame (df_bob).

        - If the numbers are different, it means some fields you wanted are missing from the result.
        - If the numbers match, you got everything you asked for.
        - If the DataFrame is empty, then Bob API returned no data at all.

        Args:
            df_bob: The DataFrame you got back from the Bob API (could be empty or missing columns).
            body_fields: The list of field names you told the API you wanted.
            schema_name: The name of the schema/table you were trying to get.

        Returns:
            tuple[str, str]:
                - A human-readable status message (for logs or debugging).
                - A status level string: "DEBUG" (all good or minor mismatch), or "ERROR" (no data at all).
        """
        if not df_bob.empty:
            requested_count = len(body_fields)
            returned_count = len(df_bob.columns)

            if requested_count != returned_count:
                status_message = (f"Schema '{schema_name}' [INFO]:\n"
                                f"Requested {requested_count} fields, got {returned_count} fields\n"
                                f"Total records: {len(df_bob)}")
                return status_message, "DEBUG"
            else:
                status_message = (f"Schema '{schema_name}': All {requested_count} requested fields "
                                f"successfully retrieved from Bob API ({len(df_bob)} records)")
                return status_message, "DEBUG"
        else:
            return f"Schema '{schema_name}' [ERROR]: No data returned from Bob API", "ERROR"

    def initialize_person_id_mapping(self) -> pd.DataFrame:
        """
        Creates a mapping DataFrame between Bob's internal person ID (`root.id`) and the employee ID in the company
        (`work.employeeIdInCompany`).

        This is a utility function for situations where you need to join or map data between endpoints/scenarios that use different
        identifiers for people. In scenarios maybe root.id is used as primary key, but in Bob, some API endpoints require you to use the employee ID.
        This function helps you convert between them.

        Note:
            - This is NOT required for the Bob SDK to function, but is a convenience tool you can call from the interface
              whenever you need to perform such a mapping.
            - The mapping is especially useful when you have data from other sources (e.g., payroll, HRIS exports) that use
              employee IDs, and you want to join or compare them with data from Bob, which often uses person IDs.

        Returns:
            pd.DataFrame: A DataFrame with two columns:
                - 'person_id': The unique person identifier in Bob (formerly `root.id`)
                - 'employee_id_in_company': The employee ID as used in your company (formerly `work.employeeIdInCompany`)

            If no people are found, returns an empty DataFrame with these columns.

        Example:
            >>> df = sdk.initialize_person_id_mapping()
            >>> # Now you can merge/join on 'person_id' or 'employee_id_in_company' as needed

        """
        # Only fetch the two fields needed for the mapping
        field_selection = ['work.employeeIdInCompany', 'root.id']

        # Use the Bob SDK to get the people data with just those fields
        valid_people, _ = self.people.get(field_selection=field_selection)

        # The SDK renames:
        #   root.id -> id
        #   work.employeeIdInCompany -> work_employee_id_in_company

        if not valid_people.empty:
            # Rename columns to standard names for mapping
            valid_people = valid_people.rename(
                columns={
                    'id': 'person_id',
                    'work_employee_id_in_company': 'employee_id_in_company'
                }
            )
            self.person_id_to_employee_id_in_company = valid_people[['person_id', 'employee_id_in_company']].copy()
        else:
            # Return empty DataFrame with expected columns if no data
            self.person_id_to_employee_id_in_company = pd.DataFrame(
                columns=['person_id', 'employee_id_in_company']
            )
        return self.person_id_to_employee_id_in_company
