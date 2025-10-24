# Docs HOWTO

Note that the file source/api.rst files needs to be manually
kept up to date in this project.

Watch changes to the docs while developing:

    sphinx-autobuild -a -b html source build/html --watch ../src

Build the docs for distribution:

    make clean html
