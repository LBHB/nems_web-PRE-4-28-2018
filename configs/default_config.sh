##  Flask settings  ##

# Enable debug mode - should *NOT* be used for a publicly-accessible site
export DEBUG="FALSE"
# Enable request forgery protection
export CSRF_ENABLED="TRUE"
# Secure key for signing CSRF data
export CSRF_SESSION_KEY="CHANGE ME TO SOMETHING SUPER SECRET"
# Secure key for signing cookies
export SECRET_KEY="ALSO CHANGE ME TO SOMETHING JUST AS SECRET"

