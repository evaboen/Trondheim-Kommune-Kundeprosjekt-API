# https://flask-marshmallow.readthedocs.io/en/latest/

from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)


PARAMETERS = { 
    "age_input": {
        "selected": ['underage (0-17)', 'young adult (18-34)'],
        "percent": 0.5
    },
    "price_input": {
        "selected": ['small', "medium"],
        "budget": 2400000
    },
    "distance_input": {
        "posistion": Point (10.39628304564158, 63.433247153410214)
    },
    "well_being_input": {
        "weight": 4
    },
    "safety_input": {
        "weight": 4
    },
    "culture_input": {
        "weight": 4
    },
    "outdoor_input": {
        "weight": 4
    },
    "transport_input": {
        "weight": 4
    },
    "walkway_input": {
        "weight": 4
    },
    "noise_traffic_input": {
        "weight": 4
    },
    "noise_other_input": {
        "weight": 4
    },
    "grocery_input": {
        "weight": 4
    }
}


def abort_if_parameter_doesnt_exist(paramater_id):
    if paramater_id not in PARAMETERS:
        abort(404, message="Parameter {} doesn't exist".format(paramater_id))

parser = reqparse.RequestParser()
parser.add_argument('paramter')


# Paramter
# shows a single todo item and lets you delete a todo item

class Parameter(Resource):
    def get(self, paramater_id):
        abort_if_parameter_doesnt_exist(paramater_id)
        return PARAMETERS[paramater_id]

    def delete(self, paramater_id):
        abort_if_parameter_doesnt_exist(paramater_id)
        del PARAMETERS[paramater_id]
        return '', 204

    def put(self, paramater_id):
        args = parser.parse_args()
        parameter = {'paramteer': args['parameter']}
        PARAMETERS[paramater_id] = parameter
        return parameter, 201


# Parameters
# shows a list of all parameteres, and lets you POST to add new tasks

class Parameters(Resource):
    def get(self):
        return PARAMETERS

    def post(self):
        args = parser.parse_args()
        paramater_id = int(max(PARAMETERS.keys()).lstrip('parameter')) + 1
        paramater_id = 'parameter%i' % paramater_id
        PARAMETERS[paramater_id] = {'parameter': args['parameter']}
        return PARAMETERS[paramater_id], 201


# Change parameter and parameter by change by user

class userParameter(Resource):
    # use put?
    def get(self, paramater_id):
        
        user_details = {
            "Age": user.age,
            "Price": user.price,
            "Nærmiljø": user.nærmiljø,
                }


if __name__ == "__main__":
        string = f"""
        Argument 1: {user_detalis[0]}
        Argument 2: {user_detalis[1]}
        Argument 3: {user_detalis[2]}
        """



##
## Actually setup the Api resource routing here
##
api.add_resource(Parameter, '/Parameter')
api.add_resource(Parameters, '/Parameters/<paramater_id>')
api.add_resource(userParameter, '/userParameter')


if __name__ == '__main__':
    app.run(debug=True)