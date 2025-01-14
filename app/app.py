from flask import Flask, render_template, request, flash, redirect, url_for
from src.extensions.milvus_connection import init_milvus
from src.services.consulting_service import consulting_main
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = 'YOUR_SECRET_KEY'  # Replace with something secure in production
    
    # Initialize extensions
    init_milvus()
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            user_input = request.form.get('user_input', '').strip()

            # If user_input is empty, flash a warning and redirect
            if not user_input:
                flash("Please enter something in the text field.")
                return redirect(url_for('index'))

            # Map gender from string to int
            gender_str = request.form.get('gender', 'not telling')
            gender_map = {
                'not telling': 0,
                'man': 1,
                'woman': 2,
                'else': 3
            }
            gender_val = gender_map.get(gender_str, 0)
            # Get seasons (multiple selection)
            seasons = request.form.getlist('seasons')
            additional_info = {'gender': gender_val, 'season': seasons}
            greeting, res_dict = consulting_main(user_input, additional_info)

            
            desc_pic_pairs = []
            for key, value in res_dict.items():
                desc_pic_pairs.append((f"For {key} part", os.path.join('static/imgs', f"{value[0]}.jpg"))) 

            return render_template('response.html',
                                greeting=greeting,
                                desc_pic_pairs=desc_pic_pairs)
        else:
            return render_template('index.html')


    @app.route('/response')
    def response_page():
        # Normally you'd redirect POST data from / to /response,
        # but for simplicity, we handle everything in index().
        return "Please submit from the index page."


    @app.route("/login")
    def login():
        return render_template('login.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

