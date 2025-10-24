# sage_setup: distribution = sagemath-database-stein-watkins-mini

from sage.misc.lazy_import import lazy_import

lazy_import('sage.databases.stein_watkins',
            ['SteinWatkinsAllData', 'SteinWatkinsPrimeData'])

del lazy_import
