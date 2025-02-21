1.) Download the repo
2.) Go to the google sheet for the data called ("Independent Stave Company Data Collection (Responses)")
3.) MAKE A COPY
4.) Make a google cloud console account if you havent
5.) make a new project called Stave Project
6.) make a new api
7.) name it and write a description (Stave Fetcher)
8.) SET IT TO EDITOR
9.) Download the key in JSON FORMAT
10.) RENAME the file to credentials.json
11.) Move the credentials.json into the folder for the stave fetcher
12.) In the file named: stave-fetcher.py, replace the name of the google sheet with the name of the COPY of the spread sheet you made
13.) in your credentials.json file, copy the "client_email"
14.) In the COPY of the data in sheets, share it to the "client_email" and make it an editor
15.) Make sure you have an activated virtual env
16.) run python3 stave-fetcher.py


P.S I did this all from memory so a step maybe be out of order or incorrect. 

contact me if it doesn't exactly work and I can assist
