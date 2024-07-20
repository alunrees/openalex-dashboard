# OpenAlex Dashboard

## Overview
The OpenAlex Dashboard is a web application that allows users to search for academic publications by fields of study using the OpenAlex API. The application is built with Flask and provides a simple interface to select fields of study, specify the number of publications, and choose the columns to include in the results.

## Features
- Search for publications by Level 0 fields of study.
- Specify the number of publications to retrieve.
- Choose which columns to include in the search results.
- Download the results as a CSV file.

## Technologies Used
- Python
- Flask
- HTML/CSS
- JavaScript
- Bootstrap
- jQuery
- Select2
- pandas
- Gunicorn (for deployment)

## Getting Started

### Prerequisites
- Python 3.6 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/alunrees/openalex-dashboard.git
    cd openalex-dashboard
    ```

2. **Create and activate a virtual environment:**

    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

### Running the Application Locally

1. **Start the Flask application:**

    ```sh
    python app.py
    ```

2. **Open your web browser and navigate to:**

    ```
    http://127.0.0.1:5000
    ```

### Deployment

To deploy the application on a production server, you can use Gunicorn and Nginx. Below is a basic example of how to set this up.

1. **Install Gunicorn:**

    ```sh
    pip install gunicorn
    ```

2. **Run Gunicorn:**

    ```sh
    gunicorn --bind 0.0.0.0:8000 app:app
    ```

3. **Configure Nginx:**

    Create an Nginx configuration file for your site (e.g., `/etc/nginx/sites-available/openalex-dashboard`):

    ```nginx
    server {
        listen 80;
        server_name your_server_domain_or_IP;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

4. **Enable the site and restart Nginx:**

    ```sh
    sudo ln -s /etc/nginx/sites-available/openalex-dashboard /etc/nginx/sites-enabled
    sudo nginx -t
    sudo systemctl restart nginx
    ```

## Usage

1. **Navigate to the application in your web browser.**
2. **Select a Level 0 field of study from the dropdown.**
3. **Specify the number of publications you want to retrieve.**
4. **Select the columns you want to include in the search results.**
5. **Click the 'Search' button to fetch and display the results.**
6. **Use the 'Download CSV' button to download the search results.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any bugs, feature requests, or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions or support, please contact [a*****@gmail.com].
