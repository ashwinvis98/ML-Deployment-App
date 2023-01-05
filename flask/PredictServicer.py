# gRPC-related dependencies
import grpc
import predict_pb2
import predict_pb2_grpc

# Outside dependencies
import pymysql
import numpy as np
import os
import json
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

# Local dependencies
from model_factory import ModelFactory


class predictServicer(predict_pb2_grpc.predictServicer):
    """
    Provides methods that implement functionality of predict server.
    """

    def __init__(self):
        """
        Builds wrapper object which contains a loaded model.
        """
        self.model_name = os.environ['MODEL_NAME']

        # Load the model
        model_factory = ModelFactory()
        self.model_wrapper = model_factory.create_model()

        # Add new table to MySQL and upload training data to it
        self.sql_insert_helper = ""
        self.load_training_data()
        

    def get_db_conn(self):
        db = pymysql.connect(
            host = '34.72.46.205',
            user = 'root',
            password = 'CUBoulder@2022',
            database = 'ml_deployment',
            charset = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor
        )

        return db

    def load_training_data(self):
        """
        Loads the training data from the .json file (which needs
        to be in a particular format) into the MySQL instance.
        """
        # Load the training data from the json file
        filename = os.environ['DATA_BUCKET'].split('/')[-1]
        f = open(filename)
        train_data = json.load(f)
        col_names = list(train_data[0].keys())

        # Form query to create the model's table
        create_sql_head = f"CREATE TABLE IF NOT EXISTS `{self.model_name}` ( "
        create_sql_tail = \
            """
            dataset VARCHAR(20),
            id  INT NOT NULL AUTO_INCREMENT,
            date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
            );
            """
        create_sql_middle = ""
        for col_name in col_names:
            create_sql_middle += col_name + ' FLOAT(53, 23), '

        create_sql = create_sql_head + create_sql_middle + create_sql_tail
        
        print(create_sql)

        # Create the table 
        db = self.get_db_conn()
        db.cursor().execute(create_sql)
        db.commit()

        # Form the query to insert the training data
        col_names.append('dataset')
        col_names_insert = ""
        for col in col_names:
            col_names_insert += col + ', '
        col_names_insert = '(' + col_names_insert[:-2] + ')'

        lst = [list(row.values()) for row in train_data]
        for row in lst:
            row.append('train')
        inserted = str([tuple(row) for row in lst])[1:-1]

        insert_sql = \
        f"""
        INSERT INTO ml_deployment.`{self.model_name}` {col_names_insert}
        VALUES {inserted};
        """
        self.sql_insert_helper = f"INSERT INTO ml_deployment.`{self.model_name}` {col_names_insert} VALUES "

        print(insert_sql)

        # Execute the INSERT query and commit the changes
        db.cursor().execute(insert_sql)
        db.commit()
        db.close()


    def Predict(self, request, context):
        """
        Implements the gRPC method.
        """
        # Reshape input to what's expected by model
        X_flat = np.asarray(request.X)
        print("divisor:", self.model_wrapper.divisor)
        n_input_examples = len(X_flat) // self.model_wrapper.divisor
        predict_dims = deepcopy(self.model_wrapper.input_dims)
        predict_dims[0] = n_input_examples
        X = X_flat.reshape(predict_dims)

        preds = self.model_wrapper.predict(X).flatten()
        self.insert_prediction_request(X_flat, preds)

        return predict_pb2.modelOutput(preds=preds)


    def insert_prediction_request(self, X, preds):
        """
        Insert a prediction request and the corresponding
        prediction into the database, along with a note 
        that this data was from a production request.
        """
        X = X.reshape(len(preds), len(X)//len(preds))
        
        inserted = []
        for i, row in enumerate(X):
            row = list(row)
            row.append(preds[i])
            row.append('prod')
            inserted.append(row)

        inserted = str([tuple(row) for row in inserted])[1:-1]
        
        prod_insert_sql = self.sql_insert_helper + inserted
        print(prod_insert_sql)

        db = self.get_db_conn()
        db.cursor().execute(prod_insert_sql)
        db.commit()
        db.close()


if __name__ == "__main__":
    """
    Start the server.
    """
    # server = predictServicer()
    # server.serve()
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    predict_pb2_grpc.add_predictServicer_to_server(predictServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()