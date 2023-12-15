import uuid
from flask import Flask, request, jsonify, abort 
from bson.objectid import ObjectId
from pymongo import MongoClient
from image_utils import convert_to_base64
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from werkzeug.exceptions import BadRequest, NotFound
import base64
# from secret import secret_key_hex

app = Flask(__name__)

app.secret_key = "sourcemonq@1234"
jwt = JWTManager(app)


# MongoDB configuration
mongo_uri = 'mongodb+srv://chakku:chakku@cluster0.fv1dext.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(mongo_uri)
db = client['doc']
users_collection = db['login']
personal_collection = db['personal']
business_collection =db['business']
bill_collection =db['bills']



@app.errorhandler(Exception)
def handle_error(e):
    status_code = 500
    response = {
        "error": "Internal server error"
    }

    if isinstance(e, (BadRequest,)):
        status_code = e.code
        response = {
            "error": e.description
        }

    return jsonify(response), status_code





  

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request', 'message': error.description}), 400

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request', 'message': error.description}), 400

@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({'error': 'Unauthorized', 'message': error.description}), 401


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found', 'message': error.description}), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500


@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        _name = data['name']
        _email = data['email']
        _password = data['pwd']
        con_password = data['c_pwd']
        
        if len(_name) < 3:
            raise BadRequest(description='Name should have at least 3 characters')
        elif "@gmail.com" not in _email:
            raise BadRequest(description='Email is not valid')
        elif len(_password) < 6:
            raise BadRequest(description='Password should have at least 6 characters')
        
        elif _password != con_password:
            raise BadRequest(description='Passwords do not match')
        
        existing_user = users_collection.find_one({'email': _email})
        if existing_user:
            return jsonify({"message": "User already exists"}), 409
        
        user_id = users_collection.insert_one({'name': _name, 'email': _email, 'pwd': _password, "c_pwd": con_password}).inserted_id
        return jsonify({'message': 'Sign Up Successful', 'user_id': str(user_id)})

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500
    


@app.route('/signin', methods=['POST', 'GET'])
def signin():    
    try:
        data = request.json
        _name = data['name']
        _password = data['pwd']

        user = users_collection.find_one({'name': _name, 'pwd': _password})
        if not user:
            raise BadRequest("create an account")

        # Create an access token
        access_token = create_access_token(identity=str(user['_id']))

        return jsonify({'message': 'Sign in successful', 'access_token': access_token}), 200

    except Exception as e:
        raise BadRequest(str(e))
      
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
# for the personal usage
@app.route("/upload", methods=['POST'])
@jwt_required()
def upload():
    try: 
        title = request.form.get('title')
        file = request.files['file']
        user_id = request.form.get('user_id')
        
        user_id = get_jwt_identity()
       
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise NotFound("User not found")

        pdf_content = base64.b64decode(file.read())
      
        file_id= personal_collection.insert_one({'content': pdf_content, 'title': title, 'user_id': ObjectId(user_id)}).inserted_id
        return jsonify({"message": "Upload successful", 'file_id': str(file_id)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/delete_per', methods=['DELETE'])                          #   for_deleteing
def delete_file():
    try:
        file_id = request.args.get("file_id")
        
        if not file_id :
            abort(400,description = 'Something is missing')
            
        if not personal_collection.find_one({"_id":ObjectId(file_id)})  : 
            abort(404, description = 'Not found')
            
        personal_collection.delete_one({"_id":ObjectId(file_id)})    
        return jsonify({"message" :"successfully"})    
            
    # except Exception as e:
    #     raise BadRequest(str(e))
    except Exception as e:
         return jsonify({"error": str(e)}), 500



@app.route("/download_per", methods=['GET'])         # for downloading 
def download_file():
    try:
        file_id = request.args.get("file_id")
        
        if not file_id :
            abort(400, description = "not")   
        
        else :                                              
            file_data = personal_collection.find_one({'_id': ObjectId(file_id)})
        
        if not file_data:
            raise NotFound("User not found")
        pdf_content = file_data['content']
        response = app.response_class(pdf_content, content_type='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename={file_data["title"]}.pdf'
        return response

    except Exception as e:
        raise BadRequest(str(e))
        
    
   
@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        user_id = request.args.get("user_id")

        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise NotFound("User not found")

        files = personal_collection.find({'user_id': ObjectId(user_id)})
          # Return a JSON response with uploaded titles and data
        
        # Prepare the list of notes
        notes = []
        for file in files :
            notes.append({
                'file_id': str(file['_id']),
                'title': file['title'],
            })

        return jsonify({'doc': notes}), 200
    except Exception as e:
        raise BadRequest(str(e))





@app.route("/view", methods=['GET'])         # for downloading 
def convert_base64_to_pdf():
    try:
        file_id = request.args.get("file_id")
                
        if not file_id :
            abort(400, description = "not")   
                
        else :                                              
              # Decode the base64 data
            pdf_data = base64.b64decode(file_id)

        # Generate a unique filename
        unique_filename = str(uuid.uuid4()) + ".pdf"

        # Save the decoded data to the current working directory
        with open(unique_filename, 'wb') as pdf_file:
            pdf_file.write(pdf_data)
        
        
        return (f"PDF file '{unique_filename}' created successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}") 

   
           
#////////////////////////////////////           finsh         //////////////////////////////////////////////////////////////////////////////


# for the business
@app.route("/upload_bus", methods=['POST'])
@jwt_required()
def upload_bus():
    try: 
        title = request.form.get('title')
        file = request.files['file']
        user_id = request.form.get('user_id')
       
        user_id = get_jwt_identity()
       
       
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise NotFound("User not found")

        pdf_content = base64.b64decode(file.read())
      
        file_id= business_collection.insert_one({'content': pdf_content, 'title': title, 'user_id': ObjectId(user_id)}).inserted_id
        return jsonify({"message": "Upload successful", 'file_id': str(file_id)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/delete_bus', methods=['DELETE'])                          #   for_deleteing
def delete_file_bus():
    try:
        file_id = request.args.get("file_id")
        
        if not file_id :
            abort(400,description = 'Something is missing')
            
        if not business_collection.find_one({"_id":ObjectId(file_id)})  : 
            abort(404, description = 'Not found')
            
        business_collection.delete_one({"_id":ObjectId(file_id)})    
        return jsonify({"message" :"successfully"})    
            
    # except Exception as e:
    #     raise BadRequest(str(e))
    except Exception as e:
         return jsonify({"error": str(e)}), 500



@app.route("/download_bus", methods=['GET'])         # for downloading 
def download_file_bus():
    try:
        file_id = request.args.get("file_id")
        
        if not file_id :
            abort(400, description = "not found")   
        
        else :                                              
            file_data = business_collection.find_one({'_id': ObjectId(file_id)})
        
        if not file_data:
            raise NotFound("User not found")
        pdf_content = file_data['content']
        response = app.response_class(pdf_content, content_type='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename={file_data["title"]}.pdf'
        return response

    except Exception as e:
        raise BadRequest(str(e))
        
    
   
@app.route('/dashboard_bus/<user_id>', methods=['GET'])
def dashboard_bus(user_id):
    try:
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise NotFound("User not found")

        files = business_collection.find({'user_id': ObjectId(user_id)})
          # Return a JSON response with uploaded titles and data
        
        # Prepare the list of notes
        notes = []
        for file in files :
            notes.append({
                'file_id': str(file['_id']),
                'title': file['title'],
            })

        return jsonify({'doc': notes}), 200
    except Exception as e:
        raise BadRequest(str(e))





@app.route("/view_bus", methods=['GET'])         # for downloading 
def convert_base64_to_pdf_bus():
    try:
        file_id = request.args.get("file_id")
        
              
        if not file_id :
            abort(400, description = "not")   
                
        else :                                              
              # Decode the base64 data
            pdf_data = base64.b64decode(file_id)

        # Generate a unique filename
        unique_filename = str(uuid.uuid4()) + ".pdf"

        # Save the decoded data to the current working directory
        with open(unique_filename, 'wb') as pdf_file:
            pdf_file.write(pdf_data)
        
        
        return (f"PDF file '{unique_filename}' created successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}") 




#///////////////////////////////////////////finsih/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////




# for the bills
@app.route("/upload_bill", methods=['POST'])
@jwt_required()
def upload_bill():
    try: 
        title = request.form.get('title')
        file = request.files['file']
        user_id = request.form.get('user_id')
       
        user_id = get_jwt_identity()
       
       
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise NotFound("User not found")

        pdf_content = base64.b64decode(file.read())
      
        file_id= bill_collection.insert_one({'content': pdf_content, 'title': title, 'user_id': ObjectId(user_id)}).inserted_id
        return jsonify({"message": "Upload successful", 'file_id': str(file_id)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/delete_bill', methods=['DELETE'])                          #   for_deleteing
def delete_file_bill():
    try:
        file_id = request.args.get("file_id")
        
        if not file_id :
            abort(400,description = 'Something is missing')
            
        if not bill_collection.find_one({"_id":ObjectId(file_id)})  : 
            abort(404, description = 'Not found')
            
        bill_collection.delete_one({"_id":ObjectId(file_id)})    
        return jsonify({"message" :"successfully"})    
            
    # except Exception as e:
    #     raise BadRequest(str(e))
    except Exception as e:
         return jsonify({"error": str(e)}), 500



@app.route("/download_bill", methods=['GET'])         # for downloading 
def download_file_bill():
    try:
        file_id = request.args.get("file_id")
        
        if not file_id :
            abort(400, description = "not found")   
        
        else :                                              
            file_data = bill_collection.find_one({'_id': ObjectId(file_id)})
        
        if not file_data:
            raise NotFound("User not found")
        pdf_content = file_data['content']
        response = app.response_class(pdf_content, content_type='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename={file_data["title"]}.pdf'
        return response

    except Exception as e:
        raise BadRequest(str(e))
        
    
   
@app.route('/dashboard_bill/<user_id>', methods=['GET'])
def dashboard_bill(user_id):
    try:
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise NotFound("User not found")

        files = bill_collection.find({'user_id': ObjectId(user_id)})
          # Return a JSON response with uploaded titles and data
        
        # Prepare the list of notes
        notes = []
        for file in files :
            notes.append({
                'file_id': str(file['_id']),
                'title': file['title'],
            })

        return jsonify({'doc': notes}), 200
    except Exception as e:
        raise BadRequest(str(e))





@app.route("/view_bill", methods=['GET'])         # for downloading 
def convert_base64_to_pdf_bill():
    try:
        file_id = request.args.get("file_id")
        
              
        if not file_id :
            abort(400, description = "not")   
                
        else :                                              
              # Decode the base64 data
            pdf_data = base64.b64decode(file_id)

        # Generate a unique filename
        unique_filename = str(uuid.uuid4()) + ".pdf"

        # Save the decoded data to the current working directory
        with open(unique_filename, 'wb') as pdf_file:
            pdf_file.write(pdf_data)
        
        
        return (f"PDF file '{unique_filename}' created successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}") 


