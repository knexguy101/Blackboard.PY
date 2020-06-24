from helpers.blackboardClient import BlackboardClient

b = BlackboardClient("https://cas.tamu.edu/cas/login", "username", "password")
b.postUsername()
password = b.postPassword()
host, sig = b.formatPasswordResponse(password)
b.doDuoSecurity(host, sig)