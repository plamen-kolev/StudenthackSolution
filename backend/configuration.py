from parse_rest.connection import register
from parse_rest.user import User
import plotly

def configure():
    APPLICATION_ID = "DotaMate"
    REST_API_KEY = "abc123"
    MASTER_KEY = "Shaman10201"
    register(APPLICATION_ID, REST_API_KEY, master_key=MASTER_KEY)
    u = User.login("dhelmet", "12345")
    plotly.tools.set_credentials_file(username='plamenkolev', api_key='PmVyrWKPavpjSKdm7N7I')