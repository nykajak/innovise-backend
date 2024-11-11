# What is Innovise?
Innovise is a community-driven website for computer science students to find new connections and opportunities. It allows for sharing of ideas and finding and exploring new horizons. We aim to provide this via enabling users to share their thoughts by way of posts and interests and carefully curating their user experience to enable users to get the most relevant content for themselves. Innovise can also serve as the starting point for job and internship hunts all thanks to our active and friendly community.

# Tech Stack
The backend uses Flask and related libraries to provide a backend server, and a mongodb server instance on atlas as a database solution. Use of Flask-Bcrypt for encryption, Flask-CORS for CORS, Flask-jwt-extended for JWT and Flask-PyMongo as an API for mongodb calls are the other libraries used in this project.

# Local Setup
- Clone this project via `git clone https://github.com/nykajak/innovise-backend.git`
- Install dependencies via `pip install -r requirements.txt`
- Set needed environment variables - `export CONN_STR = <mongodb-instance-uri>` and `export SECRET_KEY = <secret-key>`
- Launch the virtual environment and execute `python api/run.py`

# Contributors
- [nykajak](https://github.com/nykajak)
- [trex2004](https://github.com/trex2004)

### [Frontend Repo](https://github.com/trex2004/Innovise)