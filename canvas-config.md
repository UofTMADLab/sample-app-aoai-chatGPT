## Redirect URIs
	- https://aichat.dev.utoronto.io/launch/
	- https://aichat.dev.utoronto.io/launch
	(or running locally that's http://127.0.0.1:5000/launch, http://127.0.0.1:5000/launch/)
## Title
	- Azure Open AI Chat Frontend
	
## Description
	- Sample azure open ai (aoai) chat integration.
	
## Target Link URI
	- https://aichat.dev.utoronto.io/launch/
	(or use local domain for local dev)
	
## OpenID Connect Initiation Url
	- https://aichat.dev.utoronto.io/login/
	(or use local domain for local dev)
	
## JWK Method
	- Public JWK URL
	
## Public JWK URL
	- https://aichat.dev.utoronto.io/jwks/
	(or use local domain for local dev)
	
## LTI Advantage Services 
	√ Can create and view assignment data in the gradebook associated with the tool.
	
	√ Can view assignment data in the gradebook associated with the tool.
	
	√ Can view submission data for assignments associated with the tool.
	
	√ Can create and update submission results for assignments associated with the tool.
	
	√ Can retrieve user data associated with the context the tool is installed in.
	
	√ Can update public jwk for LTI services.
	
	√ Can lookup Account information
	
	√ Can view Progress records associated with the context the tool is installed in
	
## Custom Fields
	- name=$Person.name.full

## Privacy Level
	- Public
	
## Placements
	- Account Navigation
	- Link Selection
	- Assignment Selection
	
## Enable as an application

	- Open Canvas -> Admin -> (subaccount) -> Settings -> App -> by Client ID -> copy in the ID from the list of dev keys, e.g. 10000004
	
## Update Deployment ID in lti/config/tool-conf.json

- On the Canvas External Apps settings screen, click the 'gear' icon and click "deployment ID" to get the d-id.
- Put this value in a configuration in tool-conf.json in the project.


## Local SSL setup
I am running canvas.docker locally with SSL using the dinghy-http-proxy. We need to add the certificate to the ca file used by Python requests. To do this I:
- open the py venv shell with `pipenv shell`
- start the python REPL (`python`)
- `import certifi`
- `certify.where()`
This will print out the location of the ca file used by Python
- Append the contents of canvas.docker.pem (~/.dinghy/certs/canvas.docker.crt) to the end of the certify ca file.
- Also see https://incognitjoe.github.io/adding-certs-to-requests.html