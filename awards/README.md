Development
==

To generate CSS/JS:

    yarn start
    
To run development server:

    cd awards
    ./manage.py runserver


Importing data
==

Reviewers
--
    ./manage.py import_reviewers reviewers.xls
    
Entries/submissions
--

    ./manage.py import_entries

Assign ballots
--

To preview:
    
    ./manage.py init_ratings --reviews 2

To create entries in database:

    ./manage.py init_ratings --reviews 2 --commit