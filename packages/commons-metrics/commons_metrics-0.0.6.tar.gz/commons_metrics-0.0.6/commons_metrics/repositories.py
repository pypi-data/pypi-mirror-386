class ComponentRepository:
    """
    Repository class for component-specific database operations
    """
    
    def __init__(self, db_connection):
        """
        Initialize repository with database connection
        """
        self.db = db_connection
    
    def save_component(self, technical_name, id_type, status=1):
        """
        Inserts a new component into schmesys.component table
        
        Args:
            technical_name (str): Technical name of the component
            id_type (int): Component type ID
            status (int): Component status (default: 1)
        """
        cursor = None
        try:
            cursor = self.db.connection.cursor()
            
            insert_query = """
                INSERT INTO schmesys.component(technical_name, id_type, status) 
                VALUES (%s, %s, %s)
                RETURNING id;
            """
            
            cursor.execute(insert_query, (technical_name, id_type, status))
            component_id = cursor.fetchone()[0]
            self.db.commit_transaction()
            
            return component_id
            
        except Exception as e:
            self.db.rollback_transaction()
            raise Exception(f"Error saving component '{technical_name}': {str(e)}")
        finally:
            if cursor:
                cursor.close()

