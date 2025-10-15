
from flask import Blueprint, request, jsonify, session
from ..db import get_db_connection, release_db_connection, make_dict_factory

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/cvform', methods=['POST'])
def cvform():
    if 'user_id' not in session:
        return jsonify({'message': 'Authentication required. Please log in.'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    note_content = data.get('note')

    if not note_content:
        return jsonify({'message': 'Note content cannot be empty.'}), 400

    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            MERGE INTO notes n
            USING (SELECT :user_id AS user_id FROM dual) src
            ON (n.user_id = src.user_id)
            WHEN MATCHED THEN
                UPDATE SET n.content = :content, n.updated_at = SYSTIMESTAMP
            WHEN NOT MATCHED THEN
                INSERT (user_id, title, content, created_at, updated_at)
                VALUES (:user_id, :title, :content, SYSTIMESTAMP, SYSTIMESTAMP)
        """, {
            'user_id': user_id,
            'content': note_content,
            'title': 'My Note'
        })

        connection.commit()
        return jsonify({'message': 'Note saved successfully!'}), 201
    except Exception as e:
        print(f"Database Error: {e}")
        connection.rollback()
        return jsonify({'message': 'An error occurred while saving the note.'}), 500
    finally:
        if connection:
            cursor.close()
            release_db_connection(connection)

@notes_bp.route('/get-latest-note', methods=['GET'])
def get_latest_note():
    if 'user_id' not in session:
        return jsonify({'message': 'Authentication required.'}), 401

    user_id = session['user_id']
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT content FROM notes WHERE user_id = :user_id",
            user_id=user_id
        )
        
        cursor.rowfactory = make_dict_factory(cursor)
        note = cursor.fetchone()
        
        if note and note.get('content'):
            note['content'] = note['content'].read()
            return jsonify(note)
        else:
            return jsonify({'content': ''})
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({'message': 'An error occurred while fetching the note.'}), 500
    finally:
        if connection:
            cursor.close()
            release_db_connection(connection)