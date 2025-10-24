from ..utils import sf_run


def get_record(alias, sobject, record_id=None, where=None):
    """Get a record from a Salesforce object by its ID or where condition.
    
    Args:
        alias: Salesforce org alias
        sobject: Salesforce object type
        record_id: Record ID (optional)
        where: WHERE condition (optional)
    
    Returns:
        Record data from Salesforce
        
    Raises:
        ValueError: If neither record_id nor where is provided, or both are provided
    """
    # Validate that exactly one of record_id or where is provided
    if record_id is None and where is None:
        raise ValueError("Exactly one of the following must be provided: record_id, where")
    if record_id is not None and where is not None:
        raise ValueError("Exactly one of the following must be provided: record_id, where")
    
    # Build parameters
    params = {
        'target-org': alias,
        'sobject': sobject
    }
    
    # Add the appropriate parameter
    if record_id is not None:
        params['record-id'] = record_id
    else:
        params['where'] = where
    
    return sf_run('data get record', params)


def query(alias, soql_query):
    """Query Salesforce using a SOQL query."""
    return sf_run('data query', {
        'target-org': alias,
        'query': soql_query
    })

