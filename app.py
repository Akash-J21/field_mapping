from flask import Flask, request, jsonify, session, render_template
import pandas as pd
import os

app = Flask(__name__)
# Set the secret key to a random value
app.secret_key = 'd1c05e45f87b4a1f9b15c88bb8f5f90d'

app.config['downloads'] = 'downloads/'


@app.route('/', methods=['GET'])
def home():
    return render_template('home1.html')


@app.route('/download', methods=['GET', 'POST'])
def download():
    files = request.files.getlist('files[]')
    columns = []
    filename_list = []
    for file in files:
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['downloads'], filename))
            # reading
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(os.path.join(app.config['downloads'], filename))
                os.remove(os.path.join(app.config['downloads'], filename))
            else:
                df = pd.read_csv(os.path.join(app.config['downloads'], filename))
                os.path.join(app.config['downloads'], filename)

            df.columns = [filename.split('.')[0] + '.' + col for col in df.columns]
            filename = filename.split('.')[0]
            df.to_excel(f'./downloads/{filename}.xlsx')
            col_list = df.columns.to_list()

            columns.extend(col_list)
            filename_list.append(filename)

    session['columns'] = columns
    response_json = jsonify({'columns': columns})
    response_json.headers['Content-Type'] = 'application/json'
    session['df_file'] = filename_list

    return response_json


@app.route('/process', methods=['POST'])
def process():
    # Retrieve columns from session
    df_files = session.get('df_file', [])
    columns = session.get('columns', [])

    # from json
    data = request.json

    selected_columns = data.get('selectedColumns', [])
    num_joins = data.get('numberOfJoins')
    joins_data = data.get('joins')


    # Check if joins_data matches the expected criteria
    # if joins_data not in:
    #     return jsonify({"status": "error", "message": "Joins data is not matched"}), 400

    raw_table_name = [file.split('.')[0] for file in df_files]

    merged_df = pd.DataFrame()
    for count in range(num_joins):

        join_set = joins_data[count]
        left_column = join_set['dropArea1']
        right_column = join_set['dropArea2']
        join = join_set['joinType']

        # for left table
        left_df_name = left_column.split('.')[0]
        left_df_path = left_df_name + '.xlsx'
        left_df = pd.read_excel(os.path.join(app.config['downloads'], left_df_path), index_col=False)


        # for right table
        right_df_name = right_column.split('.')[0]
        right_df_path = right_df_name + '.xlsx'
        right_df = pd.read_excel(os.path.join(app.config['downloads'], right_df_path), index_col=False)

        if count > 0:
            left_df = merged_df

        merged_df = pd.merge(left_df, right_df, how=join, left_on=left_column, right_on=right_column)

    # Convert DataFrame to JSON
    final_data = merged_df.to_dict(orient='records')
    session['final_data'] = final_data
    return render_template('table.html', data=data)

@app.route('/table')
def table():
    data = session.get('final_data', {})
    # Render the next page
    return render_template('table.html', data=data)


if __name__ == "__main__":
    app.run(debug=True)
