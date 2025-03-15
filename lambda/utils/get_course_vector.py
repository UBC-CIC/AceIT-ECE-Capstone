import psycopg2

def get_course_vector(DB_CONFIG, query, course_id, num_max_results):
    # Connect to the PostgreSQL database
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query the vector database with explicit casting
        query_vectors_sql = f"""
        SELECT document_name, sourceURL, document_content, embeddings <-> %s::vector AS similarity
        FROM course_vectors_{course_id}
        ORDER BY similarity
        LIMIT %s;
        """
        # Ensure the query is passed as a string formatted like '[0.1, 0.2, 0.3]'
        formatted_query = f"[{', '.join(map(str, query))}]"  # Format the query embedding
        cursor.execute(query_vectors_sql, (formatted_query, num_max_results))
        rows = cursor.fetchall()

        results = [
            {
                "documentName": row[0],
                "sourceUrl": row[1],  # Add source_url to the result
                "documentContent": row[2],
                # "similarity": row[3]
            }
            for row in rows
        ]

        cursor.close()
        connection.close()

        return results
    except Exception as e:
        print(f"Error querying vectors: {e}")
        return "cannot connect to db"