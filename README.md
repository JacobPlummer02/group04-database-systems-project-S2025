### CS 4750 Group 04 Project

Members: Jacob Plummer (eje9bh), Jenny Schilling (xdj3kg), Heldi Valikaj (uhz6rs), Eun Soo Kang (hbw2yx)

GitHub Repository: https://github.com/JacobPlummer02/group04-database-systems-project-S2025

---

### Instructions for reproduction:
- Clone the repository at the provided url
- Install the necessary dependencies in the requirements.txt file using ```pip install -r requirements.txt```
- Create a file in the base directory titled ```.env```
- Insert the following contents into the file:
```.env
SERVER_NAME = 'group04'
USER_NAME = 'group04'
PASSWORD = 'B8daV3E5'
HOST_NAME = 'bastion.cs.virginia.edu'
```
- Apply database migrations by running ```python manage.py migrate```
- Run the developmental server with ```python manage.py runserver```
- You should be provided with a url in the terminal, copy that link and append ```/login``` to visit the login page
- Currently (in the beta version) there is no option to create a new account, so log in with the sample user:\
Username: heldi.valikaj@example.com\
Password: hashed_password
